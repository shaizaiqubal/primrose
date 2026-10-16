from unittest.mock import Mock

from backend.app.database import SessionLocal
from backend.app.models import Documents
from backend.services import entities as entity_service


def test_list_documents(client):
    response = client.get("/documents")
    assert response.status_code == 200
    assert response.json() == []


def test_create_document(authenticated_client):
    payload = {
        "title": "Test Paper",
        "abstract": "Test abstract",
        "authors": "Test Author",
        "year_published": 2024,
        "url": "https://example.com",
    }
    response = authenticated_client.post("/documents", json=payload)
    data = response.json()
    assert response.status_code in (200, 201)
    assert data["title"] == payload["title"]
    assert "id" in data


def test_create_document_processes_uploaded_document(authenticated_client, monkeypatch):
    from backend.app.routers import documents as documents_router

    process_document = Mock(return_value=[])
    monkeypatch.setattr(
        documents_router,
        "process_uploaded_document",
        process_document,
    )
    response = authenticated_client.post(
        "/documents",
        json={
            "title": "Indexed Paper",
            "abstract": "Paper abstract",
            "authors": "Author",
            "year_published": 2024,
            "url": "https://example.com",
        },
    )

    assert response.status_code == 201
    process_document.assert_called_once()
    assert process_document.call_args.args[0].id == response.json()["id"]


def test_entity_extraction_failure_embeds_document_without_entities(monkeypatch):
    with SessionLocal() as db:
        document = Documents(title="Paper", abstract="Abstract")
        db.add(document)
        db.commit()
        db.refresh(document)

    def fail_extraction(*_args):
        raise RuntimeError("extractor unavailable")

    monkeypatch.setattr(entity_service, "name_entities", fail_extraction)
    monkeypatch.setattr(entity_service, "embed_content", lambda **_kwargs: [0.1, 0.2])
    inserted = {}
    monkeypatch.setattr(
        entity_service,
        "insert_embedding",
        lambda _document, _vector, entity_ids: inserted.update(entity_ids=entity_ids),
    )
    monkeypatch.setattr(entity_service, "index_entity_vectors", lambda _entities: None)

    entity_service.process_uploaded_document(document)

    assert inserted["entity_ids"] == []
    with SessionLocal() as db:
        stored_document = db.get(Documents, document.id)
        assert stored_document is not None
        assert stored_document.embedded is True


def test_invalid_document(authenticated_client):
    response = authenticated_client.post("/documents", json={"title": "Only title"})
    assert response.status_code == 422


def test_retrieve_document(authenticated_client, client):
    payload = {
        "title": "Retrieve Paper",
        "abstract": "Retrieve abstract",
        "authors": "Test Author",
        "year_published": 2024,
        "url": "https://example.com",
    }
    created = authenticated_client.post("/documents", json=payload).json()
    response = client.get(f"/documents/{created['id']}")
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == created["id"]
    assert data["title"] == payload["title"]
    assert data["abstract"] == payload["abstract"]


def test_nonexistent_document(client):
    response = client.get("/documents/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


def test_update_existing_document(authenticated_client):
    created = authenticated_client.post(
        "/documents",
        json={
            "title": "Old Title",
            "abstract": "Old abstract",
            "authors": "Test Author",
            "year_published": 2024,
            "url": "https://example.com",
        },
    ).json()
    payload = {
        "title": "New Title",
        "abstract": "New abstract",
        "authors": "New Author",
        "year_published": 2025,
        "url": "https://example.org",
    }
    response = authenticated_client.put(f"/documents/{created['id']}", json=payload)
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == created["id"]
    assert data["title"] == payload["title"]
    assert data["abstract"] == payload["abstract"]


def test_update_nonexistent_document(authenticated_client):
    response = authenticated_client.put(
        "/documents/999999",
        json={
            "title": "New Title",
            "abstract": "New abstract",
            "authors": "New Author",
            "year_published": 2025,
            "url": "https://example.org",
        },
    )
    assert response.status_code == 404


def test_update_invalid_payload(authenticated_client):
    response = authenticated_client.put("/documents/1", json={"title": "Only title"})
    assert response.status_code == 422


def test_delete_existing_document(authenticated_client):
    created = authenticated_client.post(
        "/documents",
        json={
            "title": "Delete Title",
            "abstract": "Delete abstract",
            "authors": "Test Author",
            "year_published": 2024,
            "url": "https://example.com",
        },
    ).json()
    response = authenticated_client.delete(f"/documents/{created['id']}")
    assert response.status_code == 200


def test_delete_nonexistent_document(authenticated_client):
    response = authenticated_client.delete("/documents/999999")
    assert response.status_code == 404


def test_verify_deletion(authenticated_client, client):
    created = authenticated_client.post(
        "/documents",
        json={
            "title": "Temp Title",
            "abstract": "Temp abstract",
            "authors": "Test Author",
            "year_published": 2024,
            "url": "https://example.com",
        },
    ).json()
    authenticated_client.delete(f"/documents/{created['id']}")
    response = client.get(f"/documents/{created['id']}")
    assert response.status_code == 404
