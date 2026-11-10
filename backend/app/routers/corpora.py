from datetime import date, datetime, time, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, exists, func, select

from backend.app.database import SessionLocal
from backend.app.models import Bookmark, CorpusConfig, CorpusDocument, CorpusSync, Document_Entity, Document_Topics, Documents, Entity, Topics
from backend.app.config import ARXIV_DEFAULT_START_DATE
from backend.app.schemas import CorpusCreate, CorpusResponse, CorpusSyncRequest, CorpusSyncResponse, CorpusUpdate
from backend.services.arxiv_client import validate_categories
from backend.services.corpus_sync import SyncAlreadyRunning, create_sync
from backend.services.vector_store import COLLECTION_NAME, client as vector_client
from qdrant_client.models import PointIdsList

router = APIRouter(prefix="/corpora", tags=["corpora"])


def _get_corpus(db, corpus_id: int) -> CorpusConfig:
    corpus = db.execute(select(CorpusConfig).where(CorpusConfig.id == corpus_id)).scalar_one_or_none()
    if corpus is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corpus not found")
    return corpus


def _corpus_response(db, corpus: CorpusConfig) -> dict:
    document_count = db.execute(
        select(func.count()).select_from(CorpusDocument).where(CorpusDocument.corpus_id == corpus.id)
    ).scalar_one()
    return {
        "id": corpus.id,
        "name": corpus.name,
        "source": corpus.source,
        "categories": corpus.categories,
        "document_limit": corpus.document_limit,
        "sort_by": corpus.sort_by,
        "sort_order": corpus.sort_order,
        "start_date": corpus.start_date,
        "end_date": corpus.end_date,
        "last_synced": corpus.last_synced,
        "created_at": corpus.created_at,
        "updated_at": corpus.updated_at,
        "document_count": document_count,
    }


def _sync_response(db, sync: CorpusSync) -> dict:
    total = db.execute(
        select(func.count()).select_from(CorpusDocument).where(CorpusDocument.corpus_id == sync.corpus_id)
    ).scalar_one()
    embeddings_completed = db.execute(
        select(func.count())
        .select_from(CorpusDocument)
        .join(Documents, Documents.id == CorpusDocument.document_id)
        .where(CorpusDocument.corpus_id == sync.corpus_id, Documents.embedded.is_(True))
    ).scalar_one()
    entities_completed = db.execute(
        select(func.count())
        .select_from(CorpusDocument)
        .join(Documents, Documents.id == CorpusDocument.document_id)
        .where(CorpusDocument.corpus_id == sync.corpus_id, Documents.entities_processed.is_(True))
    ).scalar_one()
    topics_created = db.execute(
        select(func.count()).select_from(Topics).where(Topics.corpus_id == sync.corpus_id)
    ).scalar_one()
    return {
        "id": sync.id,
        "corpus_id": sync.corpus_id,
        "status": sync.status,
        "stage": sync.stage,
        "papers_discovered": sync.papers_discovered,
        "papers_inserted": sync.papers_inserted,
        "existing_papers_skipped": sync.existing_papers_skipped,
        "processing_jobs_enqueued": sync.processing_jobs_enqueued,
        "errors_encountered": sync.errors_encountered,
        "started_at": sync.started_at,
        "completed_at": sync.completed_at,
        "error_details": sync.error_details,
        "upper_cutoff": sync.upper_cutoff,
        "created_at": sync.created_at,
        "documents_total": total,
        "embeddings_completed": embeddings_completed,
        "entities_completed": entities_completed,
        "topics_created": topics_created,
    }


@router.post("", response_model=CorpusResponse, status_code=status.HTTP_201_CREATED)
def create_corpus(request: CorpusCreate):
    if request.source != "arxiv":
        raise HTTPException(status_code=400, detail="Only arxiv corpora are supported")
    try:
        categories = validate_categories(request.categories)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    with SessionLocal() as db:
        if db.execute(select(CorpusConfig.id)).scalar() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A local corpus already exists")
        start_date = request.start_date or ARXIV_DEFAULT_START_DATE
        end_date = request.end_date or datetime.now(timezone.utc).date()
        if start_date > end_date:
            raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
        corpus = CorpusConfig(name=request.name.strip(), source="arxiv", categories=categories, document_limit=request.document_limit, sort_by=request.sort_by, sort_order=request.sort_order, start_date=start_date, end_date=end_date)
        db.add(corpus)
        db.commit()
        db.refresh(corpus)
        return _corpus_response(db, corpus)


@router.get("", response_model=list[CorpusResponse])
def list_corpora():
    with SessionLocal() as db:
        corpora = list(db.execute(select(CorpusConfig).order_by(CorpusConfig.id)).scalars().all())
        return [_corpus_response(db, corpus) for corpus in corpora]


@router.get("/availability")
def corpus_availability() -> dict[str, int | bool | None]:
    """Expose whether this local Primrose instance has a corpus for public search."""
    with SessionLocal() as db:
        corpus_id = db.execute(select(CorpusConfig.id).order_by(CorpusConfig.id)).scalar()
    return {"available": corpus_id is not None, "corpus_id": corpus_id}


@router.get("/{corpus_id}", response_model=CorpusResponse)
def get_corpus(corpus_id: int):
    with SessionLocal() as db:
        return _corpus_response(db, _get_corpus(db, corpus_id))


@router.patch("/{corpus_id}", response_model=CorpusResponse)
def update_corpus(corpus_id: int, request: CorpusUpdate):
    with SessionLocal() as db:
        corpus = _get_corpus(db, corpus_id)
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
        return _corpus_response(db, corpus)


@router.post("/{corpus_id}/sync", response_model=CorpusSyncResponse, status_code=status.HTTP_202_ACCEPTED)
def sync_corpus(corpus_id: int, request: CorpusSyncRequest | None = None):
    with SessionLocal() as db:
        _get_corpus(db, corpus_id)
    try:
        sync = create_sync(corpus_id)
        with SessionLocal() as db:
            return _sync_response(db, db.get(CorpusSync, sync.id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SyncAlreadyRunning as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{corpus_id}/sync-status", response_model=CorpusSyncResponse)
def corpus_sync_status(corpus_id: int):
    with SessionLocal() as db:
        _get_corpus(db, corpus_id)
        sync = db.execute(select(CorpusSync).where(CorpusSync.corpus_id == corpus_id).order_by(CorpusSync.id.desc())).scalars().first()
        if sync is None:
            raise HTTPException(status_code=404, detail="No synchronization has been requested")
        return _sync_response(db, sync)


@router.delete("/{corpus_id}")
def delete_corpus(corpus_id: int):
    with SessionLocal() as db:
        corpus = _get_corpus(db, corpus_id)
        active = db.execute(select(CorpusSync).where(CorpusSync.corpus_id == corpus_id, CorpusSync.status.in_(["pending", "running"]))).scalar_one_or_none()
        if active:
            # Mark the job cancelled before removing its corpus. The worker
            # may still acknowledge already-published Redis jobs, but it can
            # no longer persist anything because the sync/corpus is gone.
            active.status = "cancelled"
            active.completed_at = datetime.now(timezone.utc)
            active.error_details = "Cancelled because the corpus was deleted"
        document_ids = list(db.execute(select(CorpusDocument.document_id).where(CorpusDocument.corpus_id == corpus_id)).scalars())
        if document_ids:
            vector_client.delete(collection_name=COLLECTION_NAME, points_selector=PointIdsList(points=document_ids), wait=True)
            db.execute(delete(Bookmark).where(Bookmark.document_id.in_(document_ids)))
            db.execute(delete(Document_Topics).where(Document_Topics.corpus_id == corpus_id))
            db.execute(delete(CorpusDocument).where(CorpusDocument.corpus_id == corpus_id))
            db.execute(delete(Documents).where(Documents.id.in_(document_ids)))
        db.execute(delete(Topics).where(Topics.corpus_id == corpus_id))
        db.execute(delete(CorpusSync).where(CorpusSync.corpus_id == corpus_id))
        db.delete(corpus)
        db.execute(delete(Entity).where(~exists(select(Document_Entity.entity_id).where(Document_Entity.entity_id == Entity.id))))
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

