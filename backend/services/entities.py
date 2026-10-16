import json
import logging
import time
from functools import lru_cache
from pathlib import Path
from typing import Literal, Sequence

from google import genai
from pydantic import BaseModel
from qdrant_client.models import PointStruct
from sqlalchemy import delete, func, select

from backend.app.config import GEMINI_API_KEY
from backend.app.database import SessionLocal
from backend.app.models import Document_Entity, Documents, Entity
from backend.app.schemas import (
    DocumentResponse,
    EntityPageResponse,
    EntityResponse,
    EntitySearchResult,
)
from backend.services.embed import embed_content, get_model
from backend.services.vector_store import client, ensure_collection, insert_embedding

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "entity_prompt.txt"
ENTITY_COLLECTION_NAME = "entity_vectors"
EXTRACTOR_VERSION = "v2"
ENTITY_UPSERT_BATCH_SIZE = 256
system_prompt = SYSTEM_PROMPT_PATH.read_text("utf-8")


class ExtractedEntity(BaseModel):
    name: str
    type: Literal["method", "model", "dataset", "task", "metric"]


class ExtractionResult(BaseModel):
    entities: list[ExtractedEntity]


try:
    extraction_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception:
    extraction_client = None
    logger.exception("Failed to initialize Gemini client")


@lru_cache(maxsize=1)
def _entity_name_aliases() -> dict[str, str]:
    alias_file = Path(__file__).with_name("aliases.json")
    with alias_file.open(encoding="utf-8") as file:
        mappings = json.load(file)

    aliases: dict[str, str] = {}
    for mapping in mappings:
        canonical = mapping["canonical"].strip()
        for name in [canonical, *mapping["aliases"]]:
            aliases[name.strip().casefold()] = canonical
    return aliases


def canonicalize_entity_name(name: str) -> str:
    normalized_name = name.strip()
    return _entity_name_aliases().get(normalized_name.casefold(), normalized_name)


def name_entities(title: str, abstract: str) -> ExtractionResult:
    if extraction_client is None:
        raise RuntimeError("Gemini client is not initialized")

    start_time = time.perf_counter()
    interaction = extraction_client.interactions.create(
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
    logger.info(
        "Gemini entity extraction completed in %.3f seconds",
        time.perf_counter() - start_time,
    )
    return ExtractionResult.model_validate_json(interaction.output_text) #type: ignore


def get_unlabelled() -> list[Documents]:
    has_current_version_entities = (
        select(Document_Entity.document_id)
        .where(
            Document_Entity.document_id == Documents.id,
            Document_Entity.extractor_version == EXTRACTOR_VERSION,
        )
        .exists()
    )
    statement = (
        select(Documents)
        .where(~has_current_version_entities)
        .order_by(Documents.id)
    )
    with SessionLocal() as db:
        documents = list(db.execute(statement).scalars().all())
    logger.info(
        "Found %d papers without entities from extractor %s",
        len(documents),
        EXTRACTOR_VERSION,
    )
    return documents


def save_entities(
    document_id: int,
    result: ExtractionResult,
) -> tuple[list[int], list[Entity]]:
    unique: dict[tuple[str, str], tuple[ExtractedEntity, str]] = {}
    for extracted_entity in result.entities:
        canonical_name = canonicalize_entity_name(extracted_entity.name)
        key = (canonical_name.casefold(), extracted_entity.type)
        unique.setdefault(key, (extracted_entity, canonical_name))

    entity_ids: list[int] = []
    new_entities: list[Entity] = []
    with SessionLocal.begin() as db:
        db.execute(
            delete(Document_Entity).where(
                Document_Entity.document_id == document_id
            )
        )
        for extracted_entity, canonical_name in unique.values():
            entity = db.execute(
                select(Entity).where(
                    func.lower(Entity.canonical_name) == canonical_name.casefold(),
                    Entity.type == extracted_entity.type,
                )
            ).scalar_one_or_none()
            if entity is None:
                entity = Entity(
                    canonical_name=canonical_name,
                    type=extracted_entity.type,
                    aliases=[],
                )
                db.add(entity)
                db.flush()
                new_entities.append(entity)

            entity_ids.append(entity.id)
            db.add(
                Document_Entity(
                    document_id=document_id,
                    entity_id=entity.id,
                    extractor_version=EXTRACTOR_VERSION,
                    confidence=1.0,
                )
            )

    logger.info("Saved %d entities for paper %s", len(entity_ids), document_id)
    return entity_ids, new_entities


def get_document_entity_ids(document_id: int) -> list[int]:
    statement = select(Document_Entity.entity_id).where(
        Document_Entity.document_id == document_id
    )
    with SessionLocal() as db:
        return list(db.execute(statement).scalars().all())


def get_entities(
    page: int,
    page_size: int,
    entity_type: str | None = None,
) -> EntityPageResponse:
    count_statement = select(func.count()).select_from(Entity)
    entities_statement = select(Entity)
    if entity_type:
        count_statement = count_statement.where(Entity.type == entity_type)
        entities_statement = entities_statement.where(Entity.type == entity_type)

    with SessionLocal() as db:
        total = db.scalar(count_statement) or 0
        entities = list(
            db.execute(
                entities_statement
                .order_by(Entity.canonical_name, Entity.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).scalars().all()
        )
    return EntityPageResponse(
        items=[EntityResponse.model_validate(entity) for entity in entities],
        total=total,
        page=page,
        page_size=page_size,
    )


def search_entities(query: str, limit: int) -> list[EntitySearchResult]:
    query_vector = get_model().encode(query).tolist()
    result = client.query_points(
        collection_name=ENTITY_COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_payload=False,
        with_vectors=False,
    )
    ranked_ids = [int(point.id) for point in result.points]
    scores = {int(point.id): float(point.score) for point in result.points}
    if not ranked_ids:
        return []

    with SessionLocal() as db:
        entities_by_id = {
            entity.id: entity
            for entity in db.execute(
                select(Entity).where(Entity.id.in_(ranked_ids))
            ).scalars()
        }
    return [
        EntitySearchResult(
            id=entities_by_id[entity_id].id,
            canonical_name=entities_by_id[entity_id].canonical_name,
            type=entities_by_id[entity_id].type,
            aliases=entities_by_id[entity_id].aliases or [],
            score=scores[entity_id],
        )
        for entity_id in ranked_ids
        if entity_id in entities_by_id
    ]


def get_entity_papers(entity_id: int) -> list[DocumentResponse]:
    statement = (
        select(Documents)
        .join(Document_Entity, Document_Entity.document_id == Documents.id)
        .where(Document_Entity.entity_id == entity_id)
        .order_by(Documents.id)
    )
    with SessionLocal() as db:
        documents = list(db.execute(statement).scalars().all())
    return [DocumentResponse.model_validate(document) for document in documents]


def merge_entities(
    keep_id: int,
    aliases: list[str],
    dry_run: bool = False,
) -> dict[str, int | list[str]]:
    repointed = dupes_deleted = removed = 0
    merged: set[str] = set()

    with SessionLocal.begin() as db:
        main = db.get(Entity, keep_id)
        if main is None:
            raise ValueError(f"entity {keep_id} not found")

        for alias in aliases:
            duplicates = db.execute(
                select(Entity).where(
                    func.lower(Entity.canonical_name) == alias.casefold(),
                    Entity.type == main.type,
                    Entity.id != keep_id,
                )
            ).scalars().all()
            for duplicate in duplicates:
                links = db.execute(
                    select(Document_Entity).where(
                        Document_Entity.entity_id == duplicate.id
                    )
                ).scalars().all()
                for link in links:
                    if db.get(Document_Entity, (link.document_id, keep_id)):
                        db.delete(link)
                        dupes_deleted += 1
                    else:
                        link.entity_id = keep_id
                        repointed += 1
                db.flush()
                merged.add(duplicate.canonical_name)
                db.delete(duplicate)
                removed += 1

        main.aliases = sorted(set(main.aliases or []) | merged)
        summary: dict[str, int | list[str]] = {
            "repointed": repointed,
            "dupes_deleted": dupes_deleted,
            "entities_removed": removed,
            "merged_names": sorted(merged),
        }
        if dry_run:
            db.rollback()

    return summary


def merge_configured_entities(dry_run: bool = False) -> None:
    alias_file = Path(__file__).with_name("aliases.json")
    with alias_file.open(encoding="utf-8") as file:
        mappings = json.load(file)

    for mapping in mappings:
        with SessionLocal() as db:
            canonical = db.execute(
                select(Entity).where(
                    func.lower(Entity.canonical_name)
                    == mapping["canonical"].casefold(),
                    Entity.type == mapping["type"],
                )
            ).scalar_one_or_none()
        if canonical is None:
            logger.info(
                "Canonical entity not found: %s (%s)",
                mapping["canonical"],
                mapping["type"],
            )
            continue
        summary = merge_entities(canonical.id, mapping["aliases"], dry_run)
        logger.info("Merged %s: %s", mapping["canonical"], summary)


def index_entity_vectors(entities: Sequence[Entity]) -> None:
    if not entities:
        return

    ensure_collection(name=ENTITY_COLLECTION_NAME)
    names = [entity.canonical_name for entity in entities]
    vectors = get_model().encode(
        names,
        batch_size=64,
        normalize_embeddings=True,
    )
    for start in range(0, len(entities), ENTITY_UPSERT_BATCH_SIZE):
        batch_entities = entities[start : start + ENTITY_UPSERT_BATCH_SIZE]
        batch_vectors = vectors[start : start + ENTITY_UPSERT_BATCH_SIZE]
        points = [
            PointStruct(
                id=entity.id,
                vector=vector.tolist(),
                payload={"entity": entity.canonical_name, "type": entity.type},
            )
            for entity, vector in zip(batch_entities, batch_vectors)
        ]
        client.upsert(
            collection_name=ENTITY_COLLECTION_NAME,
            wait=True,
            points=points,
        )


def index_all_entities() -> int:
    with SessionLocal() as db:
        entities = list(db.execute(select(Entity)).scalars().all())
    index_entity_vectors(entities)
    return len(entities)


def process_uploaded_document(document: Documents) -> list[int]:
    entity_ids: list[int] = []
    new_entities: list[Entity] = []
    try:
        extraction = name_entities(document.title, document.abstract)
        entity_ids, new_entities = save_entities(document.id, extraction)
    except Exception:
        logger.exception(
            "Entity extraction or persistence failed for paper %s; embedding without entities",
            document.id,
        )

    vector = embed_content(title=document.title, abstract=document.abstract)
    insert_embedding(document, vector, entity_ids=entity_ids)

    with SessionLocal.begin() as db:
        stored_document = db.get(Documents, document.id)
        if stored_document is not None:
            stored_document.embedded = True
    document.embedded = True

    index_entity_vectors(new_entities)
    return entity_ids


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for document in get_unlabelled():
        try:
            extraction = name_entities(document.title, document.abstract)
            entity_ids, new_entities = save_entities(document.id, extraction)
            index_entity_vectors(new_entities)
            logger.info("Processed paper %s with entity IDs %s", document.id, entity_ids)
            time.sleep(1)
        except Exception:
            logger.exception("Entity processing failed for paper %s", document.id)