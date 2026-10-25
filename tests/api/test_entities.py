from array import array
from types import SimpleNamespace

import pytest

from backend.app.database import SessionLocal
from backend.app.models import Bookmark, Document_Entity, Documents, Entity, User
from backend.app.routers import documents as documents_router
from backend.services import entities as entity_service
from backend.services import vector_store


def _create_entity_with_papers(name: str, paper_count: int) -> tuple[int, list[int]]:
    paper_ids = []
    with SessionLocal.begin() as db:
        entity = Entity(canonical_name=name, type="method", aliases=[])
        db.add(entity)
        db.flush()
        entity_id = entity.id
        for index in range(paper_count):
            document = Documents(
                title=f"{name} paper {index}",
                abstract="Test abstract",
                authors="Test Author",
                year_published=2024,
                url=f"https://example.com/{name}/{index}",
            )
            db.add(document)
            db.flush()
            paper_ids.append(document.id)
            db.add(
                Document_Entity(
                    document_id=document.id,
                    entity_id=entity_id,
                    extractor_version="test",
                )
            )
    return entity_id, paper_ids


def test_entity_papers_returns_joined_documents(client):
    entity_id, paper_ids = _create_entity_with_papers("SVM", 2)

    response = client.get(f"/entities/{entity_id}/papers")

    assert response.status_code == 200
    assert [paper["id"] for paper in response.json()] == paper_ids


def test_list_entities_is_paginated(client):
    _create_entity_with_papers("BERT", 1)
    _create_entity_with_papers("SVM", 1)
    _create_entity_with_papers("TF-IDF", 1)

    response = client.get("/entities", params={"page": 2, "page_size": 2})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert [entity["canonical_name"] for entity in data["items"]] == ["TF-IDF"]


def test_list_entities_filters_by_type(client):
    _create_entity_with_papers("BERT", 1)
    with SessionLocal.begin() as db:
        db.add(Entity(canonical_name="BERT model", type="model", aliases=[]))

    response = client.get("/entities", params={"type": "method"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert [entity["type"] for entity in data["items"]] == ["method"]


def test_entity_search_returns_qdrant_ranked_entities(client, monkeypatch):
    bert_id, _ = _create_entity_with_papers("BERT", 1)
    svm_id, _ = _create_entity_with_papers("SVM", 1)

    class FakeModel:
        def encode(self, query):
            assert query == "transformer model"
            return array("f", [0.1, 0.2])

    class FakeClient:
        def query_points(self, **kwargs):
            assert kwargs["collection_name"] == "entity_vectors"
            assert kwargs["query"] == pytest.approx([0.1, 0.2])
            assert kwargs["limit"] == 5
            return SimpleNamespace(
                points=[
                    SimpleNamespace(id=svm_id, score=0.91),
                    SimpleNamespace(id=bert_id, score=0.83),
                ]
            )

    monkeypatch.setattr(entity_service, "get_model", lambda: FakeModel())
    monkeypatch.setattr(entity_service, "client", FakeClient())

    response = client.get(
        "/entities/search",
        params={"q": "transformer model", "limit": 5},
    )

    assert response.status_code == 200
    results = response.json()
    assert [entity["id"] for entity in results] == [svm_id, bert_id]
    assert [entity["score"] for entity in results] == [0.91, 0.83]


def test_search_route_forwards_entity_ids(authenticated_client, monkeypatch):
    calls = {}

    def fake_search(query, entity_ids=None):
        calls.update(query=query, entity_ids=entity_ids)
        return []

    monkeypatch.setattr(documents_router, "search", fake_search)
    response = authenticated_client.get(
        "/documents/search",
        params=[("query", "classification"), ("entities", "12"), ("entities", "34")],
    )

    assert response.status_code == 200
    assert calls == {"query": "classification", "entity_ids": [12, 34]}


def test_qdrant_query_uses_must_condition_for_each_entity(monkeypatch):
    captured = {}

    class FakeClient:
        def query_points(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(points=[])

    monkeypatch.setattr(vector_store, "ensure_collection", lambda: None)
    monkeypatch.setattr(vector_store, "client", FakeClient())

    vector_store.query_documents([0.1, 0.2], entity_ids=[12, 34])

    conditions = captured["query_filter"].must
    assert [condition.key for condition in conditions] == ["entity_ids", "entity_ids"]
    assert [condition.match.value for condition in conditions] == [12, 34]


def test_document_entities_route_returns_related_entities(client):
    with SessionLocal.begin() as db:
        document = Documents(
            title="Graph neural networks",
            abstract="Training graph neural networks in practice.",
            authors="Test Author",
            year_published=2024,
            url="https://example.com/gnn",
        )
        db.add(document)
        db.flush()
        entity = Entity(canonical_name="GNNs", type="method", aliases=[])
        db.add(entity)
        db.flush()
        db.add(
            Document_Entity(
                document_id=document.id,
                entity_id=entity.id,
                extractor_version="test",
            )
        )

    response = client.get(f"/documents/{document.id}/entities")

    assert response.status_code == 200
    assert response.json()[0]["canonical_name"] == "GNNs"


def test_me_uploads_are_exposed_on_user_router(authenticated_client):
    with SessionLocal.begin() as db:
        user = db.execute(
            __import__("sqlalchemy").select(User).where(User.email == "test-user@example.com")
        ).scalar_one()
        db.add(
            Documents(
                title="My uploaded paper",
                abstract="Uploaded by me",
                authors="Test Author",
                year_published=2024,
                url="https://example.com/uploaded",
                uploaded_by=user.id,
            )
        )

    response = authenticated_client.get("/me/uploads")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "My uploaded paper"


def test_bookmark_removal_uses_document_route(authenticated_client):
    with SessionLocal.begin() as db:
        document = Documents(
            title="Bookmarked paper",
            abstract="A bookmark target",
            authors="Test Author",
            year_published=2024,
            url="https://example.com/bookmarked",
        )
        db.add(document)
        db.flush()
        db.add(Bookmark(user_id=1, document_id=document.id))

    response = authenticated_client.delete(f"/documents/{document.id}/bookmark")

    assert response.status_code == 200
    assert response.json()["message"] == "Bookmark removed successfully"


def test_send_email_accepts_email_only_payload(client):
    response = client.post("/auth/send_email", json={"email": "user@example.com"})

    assert response.status_code == 200
    assert response.json()["message"] == "Verification email sent!"