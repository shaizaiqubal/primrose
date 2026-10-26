import logging
import os
import socket
import time

from redis.exceptions import TimeoutError as RedisTimeoutError
from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models import Documents
from backend.services.embedding_queue import (
    ENTITY_CONSUMER_GROUP,
    ENTITY_STREAM_NAME,
    get_redis,
)
from backend.services.entities import process_document_entities


CONSUMER_NAME = os.getenv("ENTITY_WORKER_NAME", f"entity-{socket.gethostname()}")
BLOCK_MS = int(os.getenv("ENTITY_BLOCK_MS", "5000"))
PENDING_IDLE_MS = int(os.getenv("ENTITY_PENDING_IDLE_MS", "60000"))
RETRY_DELAY_SECONDS = int(os.getenv("ENTITY_RETRY_DELAY_SECONDS", "5"))


def process_document(document_id: int) -> None:
    with SessionLocal() as db:
        document = db.execute(
            select(Documents).where(Documents.id == document_id)
        ).scalar_one_or_none()
    if document is None:
        logging.warning("Document %s not found", document_id)
        return

    process_document_entities(document)
    logging.info("Completed entity extraction for document %s", document_id)


def ensure_consumer_group(redis_client) -> None:
    try:
        redis_client.xgroup_create(
            name=ENTITY_STREAM_NAME,
            groupname=ENTITY_CONSUMER_GROUP,
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
        logging.exception("Entity job %s failed", message_id)
        time.sleep(RETRY_DELAY_SECONDS)
        return

    redis_client.xack(ENTITY_STREAM_NAME, ENTITY_CONSUMER_GROUP, message_id)
    logging.info("Acknowledged entity job %s", message_id)


def run_worker() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    redis_client = get_redis()
    ensure_consumer_group(redis_client)
    logging.info("%s is waiting for entity jobs", CONSUMER_NAME)

    while True:
        pending = redis_client.xautoclaim(
            name=ENTITY_STREAM_NAME,
            groupname=ENTITY_CONSUMER_GROUP,
            consumername=CONSUMER_NAME,
            min_idle_time=PENDING_IDLE_MS,
            start_id="0-0",
            count=1,
        )[1]
        for message_id, fields in pending:
            handle_message(redis_client, message_id, fields)

        try:
            messages = redis_client.xreadgroup(
                groupname=ENTITY_CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={ENTITY_STREAM_NAME: ">"},
                count=1,
                block=BLOCK_MS,
            )
        except RedisTimeoutError:
            continue

        for _stream_name, entries in messages:
            for message_id, fields in entries:  # type: ignore
                handle_message(redis_client, message_id, fields)


if __name__ == "__main__":
    run_worker()
