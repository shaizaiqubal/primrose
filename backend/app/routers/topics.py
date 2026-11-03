from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models import CorpusConfig
from backend.app.schemas import DocumentResponse, TopicResponse
from backend.services.topics import get_topic, get_topic_papers, get_topics


router = APIRouter(prefix="/topics", tags=["topics"])


def _resolve_corpus_id(corpus_id: int | None) -> int:
    if corpus_id is not None:
        return corpus_id
    with SessionLocal() as db:
        resolved = db.execute(select(CorpusConfig.id).order_by(CorpusConfig.id)).scalar()
    if resolved is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No corpus is available")
    return resolved


@router.get("", response_model=list[TopicResponse])
def topics(corpus_id: int | None = Query(default=None, ge=1)):
    return get_topics(_resolve_corpus_id(corpus_id))


@router.get("/{topic_id}", response_model=TopicResponse)
def topic(topic_id: int, corpus_id: int | None = Query(default=None, ge=1)):
    return get_topic(_resolve_corpus_id(corpus_id), topic_id)


@router.get("/{topic_id}/papers", response_model=list[DocumentResponse])
def topic_papers(
    topic_id: int,
    corpus_id: int | None = Query(default=None, ge=1),
    query: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return get_topic_papers(_resolve_corpus_id(corpus_id), topic_id, query=query, page=page, page_size=page_size)
