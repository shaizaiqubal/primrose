import logging
import os
import socket
import time

from redis.exceptions import ResponseError, TimeoutError as RedisTimeoutError

from backend.services.clusters import name_clusters
from backend.services.embedding_queue import (
    TOPIC_NAMING_CONSUMER_GROUP,
    TOPIC_NAMING_STREAM_NAME,
    get_redis,
)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
CONSUMER_NAME = os.getenv("TOPIC_NAMING_WORKER_NAME", f"topic-naming-{socket.gethostname()}")
BLOCK_MS = int(os.getenv("TOPIC_NAMING_BLOCK_MS", "5000"))
PENDING_IDLE_MS = int(os.getenv("TOPIC_NAMING_PENDING_IDLE_MS", "60000"))
RETRY_DELAY_SECONDS = int(os.getenv("TOPIC_NAMING_RETRY_DELAY_SECONDS", "5"))


def ensure_consumer_group(redis_client) -> None:
    try:
        redis_client.xgroup_create(
            name=TOPIC_NAMING_STREAM_NAME,
            groupname=TOPIC_NAMING_CONSUMER_GROUP,
            id="0",
            mkstream=True,
        )
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def handle_message(redis_client, message_id: str, fields: dict[str, str]) -> None:
    corpus_id = int(fields["corpus_id"])
    try:
        name_clusters(corpus_id)
    except Exception:
        logger.exception("Topic naming failed for corpus %s; will retry", corpus_id)
        time.sleep(RETRY_DELAY_SECONDS)
        return
    redis_client.xack(TOPIC_NAMING_STREAM_NAME, TOPIC_NAMING_CONSUMER_GROUP, message_id)
    logger.info("Named available topics for corpus %s", corpus_id)


def run_worker() -> None:
    redis_client = get_redis()
    ensure_consumer_group(redis_client)
    logger.info("%s is waiting for topic naming jobs", CONSUMER_NAME)
    while True:
        try:
            pending = redis_client.xautoclaim(
                name=TOPIC_NAMING_STREAM_NAME,
                groupname=TOPIC_NAMING_CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                min_idle_time=PENDING_IDLE_MS,
                start_id="0-0",
                count=1,
            )[1]
        except ResponseError as exc:
            if "NOGROUP" not in str(exc):
                raise
            ensure_consumer_group(redis_client)
            continue
        for message_id, fields in pending:
            handle_message(redis_client, message_id, fields)
        try:
            messages = redis_client.xreadgroup(
                groupname=TOPIC_NAMING_CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={TOPIC_NAMING_STREAM_NAME: ">"},
                count=1,
                block=BLOCK_MS,
            )
        except RedisTimeoutError:
            continue
        except ResponseError as exc:
            if "NOGROUP" not in str(exc):
                raise
            ensure_consumer_group(redis_client)
            continue
        for _stream_name, entries in messages:
            for message_id, fields in entries:
                handle_message(redis_client, message_id, fields)


if __name__ == "__main__":
    run_worker()
