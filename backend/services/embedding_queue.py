import os

import redis


ENTITY_STREAM_NAME = os.getenv("ENTITY_STREAM", "entity_jobs")
ENTITY_CONSUMER_GROUP = os.getenv("ENTITY_CONSUMER_GROUP", "entity_workers")
EMBEDDING_STREAM_NAME = os.getenv("EMBEDDING_STREAM", "embedding_jobs")
EMBEDDING_CONSUMER_GROUP = os.getenv("EMBEDDING_CONSUMER_GROUP", "embedding_workers")
TOPIC_NAMING_STREAM_NAME = os.getenv("TOPIC_NAMING_STREAM", "topic_naming_jobs")
TOPIC_NAMING_CONSUMER_GROUP = os.getenv("TOPIC_NAMING_CONSUMER_GROUP", "topic_naming_workers")


def get_redis() -> redis.Redis:
    return redis.Redis(
        host=os.getenv("REDIS_HOST") or "cache",
        port=int(os.getenv("REDIS_PORT") or "6379"),
        username=os.getenv("REDIS_USER") or None,
        password=os.getenv("REDIS_PASSWORD") or None,
        decode_responses=True,
    )


def publish_embedding_job(document_id: int) -> str:
    return get_redis().xadd( #type: ignore
        EMBEDDING_STREAM_NAME,
        {"document_id": str(document_id)},
    )


def publish_entity_job(document_id: int) -> str:
    return get_redis().xadd(
        ENTITY_STREAM_NAME,
        {"document_id": str(document_id)},
    ) # type: ignore


def publish_topic_naming_job(corpus_id: int) -> str:
    return get_redis().xadd(
        TOPIC_NAMING_STREAM_NAME,
        {"corpus_id": str(corpus_id)},
    )  # type: ignore
