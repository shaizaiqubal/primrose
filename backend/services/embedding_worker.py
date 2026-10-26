import logging
import os
import socket
import time

from redis.exceptions import TimeoutError as RedisTimeoutError
from backend.app.database import SessionLocal
from backend.app.models import Documents
from backend.services.embedding_queue import (
    EMBEDDING_CONSUMER_GROUP,
    EMBEDDING_STREAM_NAME,
    get_redis,
)
from backend.services.embed import embed_content
from backend.services.entities import get_document_entity_ids
from backend.services.vector_store import insert_embedding
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s')

CONSUMER_NAME = os.getenv("WORKER_NAME", socket.gethostname())
BLOCK_MS = int(os.getenv("EMBEDDING_BLOCK_MS", "5000"))
PENDING_IDLE_MS = int(os.getenv("EMBEDDING_PENDING_IDLE_MS", "60000"))
RETRY_DELAY_SECONDS = int(os.getenv("EMBEDDING_RETRY_DELAY_SECONDS", "5"))


def process_document(document_id: int) -> None:
    logging.info("Processing document %s", document_id)
    with SessionLocal() as db:
        stmt = select(Documents).where(Documents.id == document_id)
        doc = db.execute(stmt).scalar_one_or_none()
        if doc is None:
            logging.warning("Document %s not found", document_id)
            return
        if doc.embedded:
            logging.info("Document %s already embedded", document_id)
            return
        embedding = embed_content(title=doc.title, abstract=doc.abstract)
        insert_embedding(doc, embedding, entity_ids=get_document_entity_ids(doc.id))
        with SessionLocal.begin() as db:
            stored_document = db.get(Documents, doc.id)
            if stored_document is not None:
                stored_document.embedded = True
    logging.info("Completed document %s", document_id)


def ensure_consumer_group(redis_client) -> None:
    try:
        redis_client.xgroup_create(
            name=EMBEDDING_STREAM_NAME,
            groupname=EMBEDDING_CONSUMER_GROUP,
            id="0",
            mkstream=True,
        )
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def handle_message(redis_client, message_id: str, fields: dict[str, str]) -> None:
    try:
        process_document(int(fields["document_id"]))
    except Exception:
        logging.exception("Embedding job %s failed", message_id)
        time.sleep(RETRY_DELAY_SECONDS)
        return

    redis_client.xack(EMBEDDING_STREAM_NAME, EMBEDDING_CONSUMER_GROUP, message_id)
    logging.info("Acknowledged embedding job %s", message_id)


def run_worker() -> None:
    redis_client = get_redis()
    ensure_consumer_group(redis_client)
    logging.info("%s is waiting for embedding jobs", CONSUMER_NAME)
    while True:
        autoclaimed = redis_client.xautoclaim(
            name=EMBEDDING_STREAM_NAME,
            groupname=EMBEDDING_CONSUMER_GROUP,
            consumername=CONSUMER_NAME,
            min_idle_time=PENDING_IDLE_MS,
            start_id="0-0",
            count=1,
        )
        pending = autoclaimed[1]
        for message_id, fields in pending:
            handle_message(redis_client, message_id, fields)

        try:
            messages = redis_client.xreadgroup(
                groupname=EMBEDDING_CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={EMBEDDING_STREAM_NAME: ">"},
                count=1,
                block=BLOCK_MS,
            )
        except RedisTimeoutError:
            logging.debug("Redis stream poll timed out; continuing to wait")
            continue

        for _stream_name, entries in messages:
            for message_id, fields in entries: #type: ignore
                handle_message(redis_client, message_id, fields)


if __name__ == "__main__":
    run_worker()
