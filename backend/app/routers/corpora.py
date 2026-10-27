from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models import CorpusConfig, CorpusDocument, CorpusSync, Documents, User
from backend.app.config import ARXIV_DEFAULT_START_DATE
from backend.app.routers.auth import get_current_user
from backend.app.schemas import CorpusCreate, CorpusResponse, CorpusSyncRequest, CorpusSyncResponse, CorpusUpdate
from backend.services.arxiv_client import validate_categories
from backend.services.corpus_sync import SyncAlreadyRunning, create_sync

router = APIRouter(prefix="/corpora", tags=["corpora"])


def _get_corpus(db, corpus_id: int, user_id: int) -> CorpusConfig:
    corpus = db.execute(select(CorpusConfig).where(CorpusConfig.id == corpus_id, CorpusConfig.user_id == user_id)).scalar_one_or_none()
    if corpus is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corpus not found")
    return corpus


@router.post("", response_model=CorpusResponse, status_code=status.HTTP_201_CREATED)
def create_corpus(request: CorpusCreate, user: User = Depends(get_current_user)):
    if request.source != "arxiv":
        raise HTTPException(status_code=400, detail="Only arxiv corpora are supported")
    try:
        categories = validate_categories(request.categories)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    with SessionLocal() as db:
        if db.execute(select(CorpusConfig).where(CorpusConfig.user_id == user.id)).scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Each user can have only one corpus")
        start_date = request.start_date or ARXIV_DEFAULT_START_DATE
        end_date = request.end_date or datetime.now(timezone.utc).date()
        if start_date > end_date:
            raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
        corpus = CorpusConfig(name=request.name.strip(), source="arxiv", categories=categories, document_limit=request.document_limit, sort_by=request.sort_by, sort_order=request.sort_order, user_id=user.id, start_date=start_date, end_date=end_date)
        db.add(corpus)
        db.commit()
        db.refresh(corpus)
        return corpus


@router.get("", response_model=list[CorpusResponse])
def list_corpora(user: User = Depends(get_current_user)):
    with SessionLocal() as db:
        return list(db.execute(select(CorpusConfig).where(CorpusConfig.user_id == user.id).order_by(CorpusConfig.id)).scalars().all())


@router.get("/{corpus_id}", response_model=CorpusResponse)
def get_corpus(corpus_id: int, user: User = Depends(get_current_user)):
    with SessionLocal() as db:
        return _get_corpus(db, corpus_id, user.id)


@router.patch("/{corpus_id}", response_model=CorpusResponse)
def update_corpus(corpus_id: int, request: CorpusUpdate, user: User = Depends(get_current_user)):
    with SessionLocal() as db:
        corpus = _get_corpus(db, corpus_id, user.id)
        if request.name is not None:
            corpus.name = request.name.strip()
        if request.categories is not None:
            try:
                corpus.categories = validate_categories(request.categories)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
        if request.document_limit is not None:
            corpus.document_limit = request.document_limit
        if request.sort_by is not None:
            corpus.sort_by = request.sort_by
        if request.sort_order is not None:
            corpus.sort_order = request.sort_order
        start_date = request.start_date if request.start_date is not None else (corpus.start_date or ARXIV_DEFAULT_START_DATE)
        end_date = request.end_date if request.end_date is not None else datetime.now(timezone.utc).date()
        if start_date > end_date:
            raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
        corpus.start_date = start_date
        corpus.end_date = end_date
        _prune_documents(db, corpus_id, start_date, end_date)
        db.commit()
        db.refresh(corpus)
        return corpus


@router.post("/{corpus_id}/sync", response_model=CorpusSyncResponse, status_code=status.HTTP_202_ACCEPTED)
def sync_corpus(corpus_id: int, request: CorpusSyncRequest | None = None, user: User = Depends(get_current_user)):
    with SessionLocal() as db:
        _get_corpus(db, corpus_id, user.id)
    try:
        return create_sync(corpus_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SyncAlreadyRunning as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{corpus_id}/sync-status", response_model=CorpusSyncResponse)
def corpus_sync_status(corpus_id: int, user: User = Depends(get_current_user)):
    with SessionLocal() as db:
        _get_corpus(db, corpus_id, user.id)
        sync = db.execute(select(CorpusSync).where(CorpusSync.corpus_id == corpus_id).order_by(CorpusSync.id.desc())).scalars().first()
        if sync is None:
            raise HTTPException(status_code=404, detail="No synchronization has been requested")
        return sync


@router.delete("/{corpus_id}")
def delete_corpus(corpus_id: int, user: User = Depends(get_current_user)):
    with SessionLocal() as db:
        corpus = _get_corpus(db, corpus_id, user.id)
        active = db.execute(select(CorpusSync).where(CorpusSync.corpus_id == corpus_id, CorpusSync.status.in_(["pending", "running"]))).scalar_one_or_none()
        if active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete a corpus while synchronization is running")
        db.delete(corpus)
        db.commit()
    return {"message": "Corpus deleted successfully"}


def _prune_documents(db, corpus_id: int, start_date: date, end_date: date) -> None:
    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    documents = db.execute(
        select(Documents)
        .join(CorpusDocument, CorpusDocument.document_id == Documents.id)
        .where(
            CorpusDocument.corpus_id == corpus_id,
            Documents.submitted_at.is_not(None),
            (Documents.submitted_at < start) | (Documents.submitted_at > end),
        )
    ).scalars().all()
    for document in documents:
        db.delete(document)

