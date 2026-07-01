from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.main import app
import pytest
from backend.app.database import SessionLocal
from backend.app.models import Documents


@pytest.fixture
def client():
    with TestClient(app) as client:
        with SessionLocal() as db:
            db.execute(delete(Documents))
            db.commit()
        yield client
