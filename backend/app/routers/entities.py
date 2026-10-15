from fastapi import APIRouter, Query

from backend.app.schemas import (
    DocumentResponse,
    EntityPageResponse,
    EntitySearchResult,
)
from backend.services.entities import (
    get_entities,
    get_entity_papers,
    search_entities,
)

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("", response_model=EntityPageResponse)
def list_entities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    entity_type: str | None = Query(default=None, alias="type"),
) -> EntityPageResponse:
    return get_entities(page, page_size, entity_type)


@router.get("/search", response_model=list[EntitySearchResult])
def entity_search(
    q: str = Query(min_length=1),
    limit: int = Query(default=25, ge=1, le=50),
) -> list[EntitySearchResult]:
    return search_entities(q, limit)


@router.get("/{entity_id}/papers", response_model=list[DocumentResponse])
def entity_papers(entity_id: int) -> list[DocumentResponse]:
    return get_entity_papers(entity_id)