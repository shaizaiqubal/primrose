import json

import backend.services.recommendations as recommendations


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


def test_search_returns_semantically_similar_documents(authenticated_client):
    first = _create_document(
        authenticated_client,
        "Transformer retrieval for scientific papers",
        "This paper studies transformer retrieval for scientific paper search and semantic matching.",
        "https://example.com/search-1",
    )
    second = _create_document(
        authenticated_client,
        "Semantic search with transformers for research papers",
        "This work studies semantic search with transformers for academic paper retrieval.",
        "https://example.com/search-2",
    )

    assert authenticated_client.post(f"/documents/{first['id']}/embed").status_code == 200
    assert authenticated_client.post(f"/documents/{second['id']}/embed").status_code == 200

    response = authenticated_client.get("/documents/search", params={"query": "transformer semantic search for research papers"})

    assert response.status_code == 200
    ids = [item["document"]["id"] for item in response.json()]
    assert second["id"] in ids


def test_recommendations_returns_five_papers(authenticated_client, monkeypatch):
    class _FakeInteractionResponse:
        def __init__(self, output_text):
            self.output_text = output_text

    class _FakeInteractions:
        def create(self, **kwargs):
            payload_text = kwargs["input"]
            payload = json.loads(payload_text[payload_text.index("{"): payload_text.rindex("}") + 1])
            candidate_ids = [candidate["paper_id"] for candidate in payload["candidates"][:5]]
            return _FakeInteractionResponse(
                json.dumps(
                    {
                        "recommended": [
                            {
                                "paper_id": paper_id,
                                "position": index + 1,
                                "recommendation_note": f"Why paper {paper_id} matters",
                            }
                            for index, paper_id in enumerate(candidate_ids)
                        ]
                    }
                )
            )

    class _FakeClient:
        interactions = _FakeInteractions()

    monkeypatch.setattr(recommendations, "client", _FakeClient())

    documents = [
        _create_document(
            authenticated_client,
            f"Recommendation paper {index}",
            f"This paper explores transformer retrieval and semantic search topic {index}.",
            f"https://example.com/recommend-{index}",
        )
        for index in range(6)
    ]

    for document in documents:
        assert authenticated_client.post(f"/documents/{document['id']}/embed").status_code == 200

    response = authenticated_client.get(f"/documents/{documents[0]['id']}/recommendations")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert all("recommendation_note" in item for item in data)
    assert [item["position"] for item in data] == [1, 2, 3, 4, 5]
