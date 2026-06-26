import logging
from typing import cast
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


logger = logging.getLogger(__name__)

client = QdrantClient(
    host="qdrant",
    port=6333
)

COLLECTION_NAME = "document_vectors"

def ensure_collection(vector_size: int = 384):
    try:
        collections = client.get_collections()
        existing = {c.name for c in collections.collections}
        if COLLECTION_NAME not in existing:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
    except Exception as exc:
        logger.exception("Failed to ensure Qdrant collection '%s'", COLLECTION_NAME)
        raise RuntimeError("Unable to initialize vector store collection") from exc

def insert_embedding(result, vector):
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
                    },
                )
            ],
        )
        return True
    except Exception as exc:
        logger.exception("Failed to insert embedding for document_id=%s", getattr(result, "id", None))
        raise RuntimeError("Unable to insert embedding into vector store") from exc


def get_related(id):
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
            limit=10,
            with_payload=False,
            with_vectors=False,
        )

        return [point.id for point in result.points if point.id != id]
    except Exception as exc:
        logger.exception("Failed to fetch related documents for id=%s", id)
        raise RuntimeError("Unable to fetch related documents") from exc


def query_documents(query_vector):
    try:
        ensure_collection()
        result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=10,
            with_payload=False,
            with_vectors=False,
        )

        return [point.id for point in result.points]
    except Exception as exc:
        logger.exception("Failed to query documents")
        raise RuntimeError("Unable to query documents from vector store") from exc
