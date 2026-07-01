from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Primrose.S1 server is running!"}