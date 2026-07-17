def test_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Primrose.S1 server is running!"}
