import json
import logging
from collections import Counter

import numpy as np
import redis
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from qdrant_client import QdrantClient
from sklearn.cluster import KMeans
from sqlalchemy import or_, select

from backend.app.cache import TTL, cache
from backend.app.config import (
    QDRANT_API_KEY,
    QDRANT_COLLECTION_NAME,
    QDRANT_PORT,
    QDRANT_URL,
)
from backend.app.database import SessionLocal
from backend.app.models import Documents, Document_Topics, Topics
from backend.app.schemas import DocumentResponse, TopicResponse

logger = logging.getLogger(__name__)


def _get_vector_client() -> QdrantClient:
    return QdrantClient(
        url=QDRANT_URL,
        port=QDRANT_PORT,
        api_key=QDRANT_API_KEY,
        check_compatibility=False,
    )


def _get_embeddings() -> tuple[list[list[float]], list[int]]:
    result = _get_vector_client().query_points(
        collection_name=QDRANT_COLLECTION_NAME,
        with_vectors=True,
        with_payload=False,
        limit=10000,
    )
    return (
        [point.vector for point in result.points],
        [point.id for point in result.points],
    )


def run_topic_pipeline(n_topics: int = 100) -> int:
    """Cluster stored document embeddings and persist topic assignments."""
    embeddings, document_ids = _get_embeddings()
    if not embeddings:
        logger.info("No embeddings available for topic generation")
        return 0

    topic_count = min(n_topics, len(embeddings))
    model = KMeans(
        n_clusters=topic_count,
        init="k-means++",
        n_init=1,
        max_iter=300,
        random_state=42,
    ).fit(np.asarray(embeddings))
    counts = Counter(model.labels_)

    with SessionLocal.begin() as db:
        db.query(Document_Topics).delete()
        db.query(Topics).delete()
        db.add_all(
            Topics(
                cluster_id=cluster_id,
                cluster_name=None,
                paper_count=counts[cluster_id],
                centroid=centroid.tolist(),
            )
            for cluster_id, centroid in enumerate(model.cluster_centers_)
        )
        db.add_all(
            Document_Topics(id=document_id, cluster_id=int(cluster_id))
            for document_id, cluster_id in zip(document_ids, model.labels_)
        )

    _clear_topic_cache()
    logger.info("Generated %s topics for %s documents", topic_count, len(document_ids))
    return topic_count


def _clear_topic_cache() -> None:
    try:
        keys = list(cache.scan_iter("topics:*") )
        if keys:
            cache.delete(*keys)
    except redis.RedisError as exc:
        logger.warning("Failed to clear topic cache: %s", exc)


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


def get_topic_papers(
    topic_id: int,
    query: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[DocumentResponse]:
    normalized_query = query.strip() if query else ""
    key = f"topics:papers:{topic_id}:{normalized_query}:{page}:{page_size}"
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
        if normalized_query:
            stmt = stmt.where(
                or_(
                    Documents.title.ilike(f"%{normalized_query}%"),
                    Documents.abstract.ilike(f"%{normalized_query}%"),
                )
            )
        result = list(
            db.execute(
                stmt.order_by(Documents.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).scalars().all()
        )

    if not result:
        if normalized_query:
            return []
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
