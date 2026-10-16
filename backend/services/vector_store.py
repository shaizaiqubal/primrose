import logging
from collections.abc import Sequence
from typing import cast
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)
from backend.app.config import (
    QDRANT_API_KEY,
    QDRANT_COLLECTION_NAME,
    QDRANT_PORT,
    QDRANT_URL,
)

logger = logging.getLogger(__name__)


client = QdrantClient(
    url=QDRANT_URL,
    port=QDRANT_PORT,
    api_key=QDRANT_API_KEY,
    check_compatibility=False
)

COLLECTION_NAME = QDRANT_COLLECTION_NAME

def ensure_collection(vector_size: int = 384, name: str = COLLECTION_NAME):
    try:
        collections = client.get_collections()
        existing = {c.name for c in collections.collections}
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info("Initailized collection '%s'", name)
    except Exception as exc:
        logger.exception("Failed to ensure Qdrant collection '%s'", name)
        raise RuntimeError("Unable to initialize vector store collection") from exc

def insert_embedding(result, vector, entity_ids: list[int] | None = None):
    try:
        ensure_collection()
        client.upsert(
            collection_name=COLLECTION_NAME,
            wait=True,
            points=[
                PointStruct(
                    id=result.id,
                    vector=vector.tolist(),
                    payload={
                        "document_id": result.id,
                        "year_published": result.year_published,
                        "authors": result.authors,
                        "entity_ids": entity_ids or [],
                    },
                )
            ],
        )
        return True
    except Exception as exc:
        logger.exception("Failed to insert embedding for document_id=%s", getattr(result, "id", None))
        raise RuntimeError("Unable to insert embedding into vector store") from exc


def delete_embedding(id):
    try:
        ensure_collection()
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=PointIdsList(points=[id]),
            wait=True,
        )
        return True
    except Exception as exc:
        logger.exception("Failed to delete embedding for document_id=%s", id)
        raise RuntimeError("Unable to delete embedding from vector store") from exc


def get_related_ids(id):
    try:
        ensure_collection()
        points = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[id],
            with_vectors=True,
            with_payload=False,
        )

        if not points:
            return []

        record = points[0]
        if record.vector is None:
            raise ValueError("Retrieved point has no vector")

        query_vector = cast(list[float], record.vector)

        result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=11,
            with_payload=False,
            with_vectors=False,
        )

        return [point.id for point in result.points if point.id != id]
    except Exception as exc:
        logger.exception("Failed to fetch related documents for id=%s", id)
        raise RuntimeError("Unable to fetch related documents") from exc


def query_documents(query_vector, entity_ids: Sequence[int] | None = None):
    try:
        ensure_collection()
        query_filter = None
        if entity_ids:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="entity_ids",
                        match=MatchValue(value=entity_id),
                    )
                    for entity_id in entity_ids
                ]
            )
        result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=10,
            with_payload=False,
            with_vectors=False,
        )

        return [point.id for point in result.points]
    except Exception as exc:
        logger.exception("Failed to query documents")
        raise RuntimeError("Unable to query documents from vector store") from exc
