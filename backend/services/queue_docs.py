import json
from functools import lru_cache
from google.cloud import pubsub_v1
from backend.app.models import Documents

PROJECT_ID: str = "project-4c950df3-61d0-44ee-a30"
TOPIC_NAME: str = "primrose-embeddings"

@lru_cache(maxsize=1)
def get_publisher() -> pubsub_v1.PublisherClient:
    return pubsub_v1.PublisherClient()


@lru_cache(maxsize=1)
def get_topic_path() -> str:
    return get_publisher().topic_path(PROJECT_ID, TOPIC_NAME)

def queue_documents(document: Documents) -> str:
    document_id = int(document.id)
    payload: dict[str, int] = {"document_id": document_id}

    future = get_publisher().publish(
        get_topic_path(),
        data=json.dumps(payload).encode("utf-8"),
    )

    return future.result()
