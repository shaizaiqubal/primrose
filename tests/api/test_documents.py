def test_list_documents(client):
    response = client.get("/documents")
    assert response.status_code == 200
    assert response.json() == []


def test_create_document(client):
    payload = {
        "title": "Test Paper",
        "abstract": "Test abstract",
        "authors": "Test Author",
        "year_published": 2024,
        "url": "https://example.com",
    }
    response = client.post("/documents", json=payload)
    data = response.json()
    assert response.status_code in (200, 201)
    assert data["title"] == payload["title"]
    assert "id" in data


def test_invalid_document(client):
    response = client.post("/documents", json={"title": "Only title"})
    assert response.status_code == 422


def test_retrieve_document(client):
    payload = {
        "title": "Retrieve Paper",
        "abstract": "Retrieve abstract",
        "authors": "Test Author",
        "year_published": 2024,
        "url": "https://example.com",
    }
    created = client.post("/documents", json=payload).json()
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


def test_update_existing_document(client):
    created = client.post(
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
    response = client.put(f"/documents/{created['id']}", json=payload)
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == created["id"]
    assert data["title"] == payload["title"]
    assert data["abstract"] == payload["abstract"]


def test_update_nonexistent_document(client):
    response = client.put(
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


def test_update_invalid_payload(client):
    response = client.put("/documents/1", json={"title": "Only title"})
    assert response.status_code == 422


def test_delete_existing_document(client):
    created = client.post(
        "/documents",
        json={
            "title": "Delete Title",
            "abstract": "Delete abstract",
            "authors": "Test Author",
            "year_published": 2024,
            "url": "https://example.com",
        },
    ).json()
    response = client.delete(f"/documents/{created['id']}")
    assert response.status_code == 200


def test_delete_nonexistent_document(client):
    response = client.delete("/documents/999999")
    assert response.status_code == 404


def test_verify_deletion(client):
    created = client.post(
        "/documents",
        json={
            "title": "Temp Title",
            "abstract": "Temp abstract",
            "authors": "Test Author",
            "year_published": 2024,
            "url": "https://example.com",
        },
    ).json()
    client.delete(f"/documents/{created['id']}")
    response = client.get(f"/documents/{created['id']}")
    assert response.status_code == 404
