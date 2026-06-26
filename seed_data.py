import json
from pathlib import Path

from sqlalchemy import select

from backend.app.database import Base, SessionLocal, engine
from backend.app.models import Documents


SEED_DATA_PATH = Path(__file__).with_name("primrose_seed_data.json")


def load_seed_documents() -> list[dict]:
    with SEED_DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def seed_database() -> None:
    Base.metadata.create_all(bind=engine)

    seed_documents = load_seed_documents()

    with SessionLocal() as db:
        existing_titles = set(
            db.execute(select(Documents.title)).scalars().all()
        )
        missing_rows = [
            Documents(**row)
            for row in seed_documents
            if row["title"] not in existing_titles
        ]

        if not missing_rows:
            print(f"Seed skipped: {len(existing_titles)} seeded documents already exist.")
            return

        db.add_all(missing_rows)
        db.commit()
        print(f"Seeded {len(missing_rows)} documents.")


if __name__ == "__main__":
    seed_database()
