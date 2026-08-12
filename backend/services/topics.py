import json
import logging

import redis
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from backend.app.cache import TTL, cache
from backend.app.database import SessionLocal
from backend.app.models import Documents, Document_Topics, Topics
from backend.app.schemas import DocumentResponse, TopicResponse

logger = logging.getLogger(__name__)


def get_topics() -> list[TopicResponse]:
    key = "topics:topics"
    try:
        payload = cache.get(key)
    except redis.RedisError as exc:
        payload = None
        logger.warning("Redis cache unavailable for topics list: %s", exc)

    if payload:
        cached_topics = jsonable_encoder(json.loads(payload))
        return [TopicResponse.model_validate(item) for item in cached_topics]

    with SessionLocal() as db:
        stmt = select(Topics).order_by(Topics.paper_count.desc())
        result = db.execute(stmt).scalars().all()

    payload = json.dumps(jsonable_encoder(result))
    try:
        cache.set(key, payload, ex=TTL)
    except redis.RedisError as exc:
        logger.warning("Failed to cache topics list: %s", exc)

    return [TopicResponse.model_validate(jsonable_encoder(topic)) for topic in result]


def get_topic(topic_id: int) -> TopicResponse:
    key = f"topics:{topic_id}"
    try:
        payload = cache.get(key)
    except redis.RedisError as exc:
        payload = None
        logger.warning("Redis cache unavailable for topic %s: %s", topic_id, exc)

    if payload:
        cached_topic = jsonable_encoder(json.loads(payload))
        return TopicResponse.model_validate(cached_topic)

    with SessionLocal() as db:
        stmt = select(Topics).where(Topics.cluster_id == topic_id)
        result = db.execute(stmt).scalar_one_or_none()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    payload = json.dumps(jsonable_encoder(result))
    try:
        cache.set(key, payload, ex=TTL)
    except redis.RedisError as exc:
        logger.warning("Failed to cache topic %s: %s", topic_id, exc)

    return TopicResponse.model_validate(jsonable_encoder(result))


def get_topic_papers(topic_id: int) -> list[DocumentResponse]:
    key = f"topics:papers:{topic_id}"
    try:
        payload = cache.get(key)
    except redis.RedisError as exc:
        payload = None
        logger.warning("Redis cache unavailable for topic papers %s: %s", topic_id, exc)

    if payload:
        cached_papers = jsonable_encoder(json.loads(payload))
        return [DocumentResponse.model_validate(item) for item in cached_papers]

    with SessionLocal() as db:
        stmt = (
            select(Documents)
            .join(Document_Topics, Documents.id == Document_Topics.id)
            .where(Document_Topics.cluster_id == topic_id)
        )
        result = db.execute(stmt).scalars().all()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic is empty",
        )

    payload = json.dumps(jsonable_encoder(result))
    try:
        cache.set(key, payload, ex=TTL)
    except redis.RedisError as exc:
        logger.warning("Failed to cache topic papers %s: %s", topic_id, exc)

    return [DocumentResponse.model_validate(item) for item in jsonable_encoder(result)]
