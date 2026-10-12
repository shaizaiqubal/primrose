import logging
import time
from pathlib import Path
from typing import Literal

from google import genai
from pydantic import BaseModel
from sqlalchemy import delete, func, select

from backend.app.config import GEMINI_API_KEY
from backend.app.database import SessionLocal
from backend.app.models import Document_Entity, Documents, Entity

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "entity_prompt.txt"
EXTRACTOR_VERSION = "v1"

system_prompt = SYSTEM_PROMPT_PATH.read_text("utf-8")

class ExtractedEntity(BaseModel):
    name: str
    type: Literal["method", "model", "dataset", "task", "metric"]

class ExtractionResult(BaseModel):
    entities: list[ExtractedEntity]

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as exc:
    client = None
    logger.exception("Failed to initialize Gemini client: %s", exc)


def name_entities(title: str, abstract: str) -> ExtractionResult:
    if client is None:
        logger.error("Cannot extract entities because the Gemini client is unavailable")
        raise RuntimeError("Gemini client is not initialized")

    start_time = time.perf_counter()
    try:
        interaction = client.interactions.create(
            model="gemini-3.1-flash-lite",
            input=f"""
                Below is the current paper and its abstract:
                {title}

                {abstract}
                """,
            system_instruction=system_prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": ExtractionResult.model_json_schema(),
            },
        )
    except Exception:
        logger.exception("Gemini entity extraction request failed for paper '%s'", title)
        raise

    latency_seconds = time.perf_counter() - start_time
    logger.info("Gemini entity extraction completed in %.3f seconds", latency_seconds)
    try:
        result = ExtractionResult.model_validate_json(interaction.output_text)  # type: ignore[arg-type]
    except Exception:
        logger.exception("Failed to parse Gemini entity response for paper '%s'", title)
        raise
    return result


def get_unlabelled() -> list[Documents]:
    try:
        with SessionLocal() as db:
            has_current_version_entities = (
                select(Document_Entity.document_id)
                .where(
                    Document_Entity.document_id == Documents.id,
                    Document_Entity.extractor_version == EXTRACTOR_VERSION,
                )
                .exists()
            )
            stmt = (
                select(Documents)
                .where(~has_current_version_entities)
                .order_by(Documents.id)
            )

            docs = list(db.execute(stmt).scalars().all())
        logger.info("Found %d papers without entities from extractor %s", len(docs), EXTRACTOR_VERSION)
        return docs
    except Exception:
        logger.exception("Failed to fetch papers without entities for extractor %s", EXTRACTOR_VERSION)
        raise


def save_entities(doc_id: int, result: ExtractionResult) -> list[ExtractedEntity]:
    seen = set()
    unique = []
    for ent in result.entities:
        key = (ent.name.strip().lower(), ent.type)
        if key in seen:
            continue
        seen.add(key)
        unique.append(ent)

    try:
        with SessionLocal.begin() as db:
            db.execute(delete(Document_Entity).where(Document_Entity.document_id == doc_id))
            for ent in unique:
                normalized_name = ent.name.strip().lower()
                entity = db.execute(
                    select(Entity).where(
                        func.lower(Entity.canonical_name) == normalized_name,
                        Entity.type == ent.type,
                    )
                ).scalar_one_or_none()

                if entity is None:
                    entity = Entity(
                        canonical_name=ent.name.strip(),
                        type=ent.type,
                        aliases=[],
                    )
                    db.add(entity)
                    db.flush()

                db.add(
                    Document_Entity(
                        document_id=doc_id,
                        entity_id=entity.id,
                        extractor_version=EXTRACTOR_VERSION,
                        confidence=1.0,
                    )
                )

        logger.info("Saved %d entities for paper %s", len(unique), doc_id)
    except Exception:
        logger.exception("Failed to save entities for paper %s", doc_id)
        raise

    return unique



if __name__ == '__main__' :
    logging.basicConfig(level=logging.INFO)
    unnamed = get_unlabelled()

    for doc in unnamed[:3]:
        if not (doc.abstract or "").strip():
            logger.info("Skipping paper %s because it has no abstract", doc.id)
            continue
        if "survey" in doc.title.lower() or "review" in doc.title.lower():
            logger.info("Skipping review paper %s", doc.id)
            continue
        try:
            entities = name_entities(doc.title, doc.abstract)
            save_entities(doc.id, entities)
        except Exception:
            logger.exception("Entity processing failed for paper %s", doc.id)