import uuid

import pytest
from qdrant_client.models import PointIdsList
from sqlalchemy import delete

from backend.app.database import SessionLocal
from backend.app.models import Documents
import backend.services.vector_store as vector_store

qdrant_client = vector_store.client


@pytest.fixture(scope="module", autouse=True)
def use_test_collection():
    original_collection = vector_store.COLLECTION_NAME
    test_collection = f"{original_collection}_test_{uuid.uuid4().hex[:8]}"
    vector_store.COLLECTION_NAME = test_collection
    try:
        yield test_collection
    finally:
        try:
            qdrant_client.delete_collection(test_collection)
        except Exception:
            pass
        vector_store.COLLECTION_NAME = original_collection


def _create_document(client, title, abstract, url):
    response = client.post(
        "/documents",
        json={
            "title": title,
            "abstract": abstract,
            "authors": "Test Author",
            "year_published": 2024,
            "url": url,
        },
    )
    assert response.status_code == 201
    return response.json()

def _cleanup_documents(*documents):
    ids = [document["id"] for document in documents if document]
    if not ids:
        return
    with SessionLocal() as db:
        db.execute(delete(Documents).where(Documents.id.in_(ids)))
        db.commit()
    try:
        qdrant_client.delete(
            collection_name=vector_store.COLLECTION_NAME,
            points_selector=PointIdsList(points=ids),
        )
    except Exception:
        pass


def test_embed_document_happy_path(client):
    document = None
    try:
        document = _create_document(
            client,
            "Graph neural networks for citation analysis",
            "This paper studies graph neural networks for citation analysis in scientific literature.",
            "https://example.com/embed-happy",
        )
        response = client.post(f"/documents/{document['id']}/embed")

        assert response.status_code == 200
        assert response.json() == {"message": "Embedded successfully"}
    finally:
        _cleanup_documents(document)


def test_embed_nonexistent_document(client):
    response = client.post("/documents/999999/embed")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


def test_reembedding_document_succeeds_twice(client):
    document = None
    try:
        document = _create_document(
            client,
            "Re-embedding test paper",
            "This paper is embedded twice to verify current API behavior.",
            "https://example.com/reembed",
        )
        first = client.post(f"/documents/{document['id']}/embed")
        second = client.post(f"/documents/{document['id']}/embed")

        assert first.status_code == 200
        assert second.status_code == 200
    finally:
        _cleanup_documents(document)


def test_embed_updates_embedded_flag(client):
    document = None
    try:
        document = _create_document(
            client,
            "Embedding flag paper",
            "This paper verifies the embedded flag changes after embedding.",
            "https://example.com/embed-flag",
        )
        before = client.get(f"/documents/{document['id']}")
        embed_response = client.post(f"/documents/{document['id']}/embed")
        after = client.get(f"/documents/{document['id']}")

        assert before.status_code == 200
        assert before.json()["embedded"] is False
        assert embed_response.status_code == 200
        assert after.status_code == 200
        assert after.json()["embedded"] is True
    finally:
        _cleanup_documents(document)


def test_embed_with_invalid_document_id_returns_422(client):
    response = client.post("/documents/not-an-int/embed")

    assert response.status_code == 422


def test_embed_multiple_documents(client):
    documents = []
    try:
        documents = [
            _create_document(
                client,
                f"Batch embedding paper {index}",
                f"This is batch embedding document {index}.",
                f"https://example.com/multi-{index}",
            )
            for index in range(3)
        ]

        for document in documents:
            response = client.post(f"/documents/{document['id']}/embed")
            assert response.status_code == 200
            assert response.json() == {"message": "Embedded successfully"}
            response_get = client.get(f"/documents/{document['id']}")
            assert response_get.json()["embedded"] is True
    finally:
        _cleanup_documents(*documents)


def test_embed_end_to_end_related_documents(client):
    first = second = None
    try:
        first = _create_document(
            client,
            "Transformer retrieval for academic papers",
            "This paper studies transformer retrieval for academic papers and semantic search.",
            "https://example.com/end-to-end-1",
        )
        second = _create_document(
            client,
            "Semantic search with transformers for research papers",
            "This work studies semantic search with transformers for academic paper retrieval.",
            "https://example.com/end-to-end-2",
        )

        assert client.post(f"/documents/{first['id']}/embed").status_code == 200
        assert client.post(f"/documents/{second['id']}/embed").status_code == 200

        response = client.get(f"/documents/{first['id']}/related")
        ids = [item["id"] for item in response.json()]

        assert response.status_code == 200
        assert second["id"] in ids
    finally:
        _cleanup_documents(first, second)
