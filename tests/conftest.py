import os
from time import sleep
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parents[1]

os.environ["TESTING"] = "1"

from backend.app.config import DATABASE_URL, QDRANT_COLLECTION_NAME, QDRANT_URL
from backend.app.database import Base, SessionLocal, engine
from backend.app.main import app
from backend.app.models import User
from backend.app.security import create_access_token
import backend.services.vector_store as vector_store


def _wait_for_qdrant_ready() -> None:
    for _ in range(30):
        try:
            vector_store.client.get_collections()
            return
        except Exception:
            sleep(1)
    raise RuntimeError("Qdrant test container did not become ready in time")


def _reset_database() -> None:
    with engine.begin() as connection:
        Base.metadata.drop_all(bind=connection)
        Base.metadata.create_all(bind=connection)


def _reset_qdrant_collection() -> None:
    try:
        vector_store.client.delete_collection(collection_name=QDRANT_COLLECTION_NAME)
    except Exception:
        pass
    vector_store.ensure_collection()


def _safe_database_label(database_url: str) -> str:
    parsed = make_url(database_url)
    host = parsed.host or "unknown-host"
    port = parsed.port or "unknown-port"
    database = parsed.database or "unknown-db"
    return f"{parsed.drivername}://{host}:{port}/{database}"


@pytest.fixture(scope="session", autouse=True)
def isolated_test_environment():
    dev_env = dotenv_values(REPO_ROOT / ".env")
    if DATABASE_URL == dev_env.get("DATABASE_URL"):
        raise RuntimeError("Refusing to run tests against the development PostgreSQL URL")
    if QDRANT_URL == dev_env.get("QDRANT_URL"):
        raise RuntimeError("Refusing to run tests against the development Qdrant URL")
    if QDRANT_COLLECTION_NAME == dev_env.get("QDRANT_COLLECTION_NAME", "document_vectors"):
        raise RuntimeError("Refusing to run tests against the development Qdrant collection")

    print(f"[tests] PostgreSQL: {_safe_database_label(DATABASE_URL)}") # type: ignore
    print(f"[tests] Qdrant: {QDRANT_URL} collection={QDRANT_COLLECTION_NAME}")

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    _wait_for_qdrant_ready()
    _reset_database()
    _reset_qdrant_collection()

    yield


@pytest.fixture(autouse=True)
def clean_test_state():
    _reset_database()
    _reset_qdrant_collection()
    yield
    _reset_database()
    _reset_qdrant_collection()


@pytest.fixture
def client(clean_test_state, monkeypatch):
    import backend.app.routers.documents as documents_router

    monkeypatch.setattr(
        documents_router,
        "queue_documents",
        lambda document: "pubsub-disabled",
    )

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def authenticated_client(client):
    with SessionLocal() as db:
        user = User(
            email="test-user@example.com",
            password_hash="test-password-hash",
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        access_token = create_access_token(user.id)

    client.headers.update({"Authorization": f"Bearer {access_token}"})
    return client
