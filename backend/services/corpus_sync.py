from __future__ import annotations

import logging
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time as datetime_time, timezone

from sqlalchemy import select

from backend.app.config import ARXIV_DEFAULT_START_DATE, ARXIV_PAGE_SIZE
from backend.app.database import SessionLocal
from backend.app.models import CorpusConfig, CorpusDocument, CorpusSync, Documents
from backend.services.arxiv_client import ArxivClient
from backend.services.embedding_queue import publish_embedding_job, publish_entity_job

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="corpus-sync")


class SyncAlreadyRunning(RuntimeError):
    pass


def create_sync(corpus_id: int) -> CorpusSync:
    with SessionLocal() as db:
        corpus = db.execute(select(CorpusConfig).where(CorpusConfig.id == corpus_id).with_for_update()).scalar_one_or_none()
        if corpus is None:
            raise LookupError("Corpus not found")
        active = db.execute(select(CorpusSync).where(CorpusSync.corpus_id == corpus_id, CorpusSync.status.in_(["pending", "running"]))).scalar_one_or_none()
        if active:
            raise SyncAlreadyRunning("A synchronization is already running for this corpus")
        sync = CorpusSync(corpus_id=corpus_id)
        db.add(sync)
        db.commit()
        db.refresh(sync)
        sync_id = sync.id
    executor.submit(run_sync, sync_id)
    return sync


def run_sync(sync_id: int, client: ArxivClient | None = None) -> None:
    client = client or ArxivClient()
    now = datetime.now(timezone.utc)
    try:
        with SessionLocal() as db:
            sync = db.get(CorpusSync, sync_id)
            if sync is None:
                return
            corpus = db.get(CorpusConfig, sync.corpus_id)
            if corpus is None:
                raise LookupError("Corpus not found")
            sync.status = "running"
            sync.started_at = now
            sync.upper_cutoff = now
            categories = list(corpus.categories)
            document_limit = corpus.document_limit
            sort_by = corpus.sort_by
            sort_order = corpus.sort_order
            corpus_id = corpus.id
            start_date = corpus.start_date or ARXIV_DEFAULT_START_DATE
            db.commit()

        end_date = datetime.now(timezone.utc).date()
        start = datetime.combine(start_date, datetime_time.min, tzinfo=timezone.utc)
        end = datetime.combine(end_date, datetime_time.max, tzinfo=timezone.utc)
        offset = 0
        seen: set[str] = set()
        document_ids: list[int] = []
        with SessionLocal() as db:
            current_count = db.execute(
                select(CorpusDocument.document_id).where(CorpusDocument.corpus_id == corpus_id)
            ).all()
        added_count = len(current_count)
        while True:
            if added_count >= document_limit:
                break
            page, total = client.fetch_page(categories, offset, ARXIV_PAGE_SIZE, start, end, sort_by, sort_order)
            if not page:
                break
            unique_page = [paper for paper in page if paper.arxiv_id not in seen]
            seen.update(paper.arxiv_id for paper in unique_page)
            new_ids, added = _persist_page(sync_id, unique_page, document_limit - added_count)
            document_ids.extend(new_ids)
            added_count += added
            offset += len(page)
            if total is not None and offset >= total:
                break
            if len(page) < ARXIV_PAGE_SIZE:
                break
        _wait_for_embeddings(document_ids)
        subprocess.run([sys.executable, "-m", "backend.services.topic_worker"], check=True)
        with SessionLocal() as db:
            sync = db.get(CorpusSync, sync_id)
            corpus = db.get(CorpusConfig, sync.corpus_id) if sync else None
            if sync is None or corpus is None:
                return
            sync.status = "completed"
            sync.completed_at = datetime.now(timezone.utc)
            corpus.last_synced = now
            corpus.end_date = end_date
            db.commit()
    except Exception as exc:
        logger.exception("Corpus sync %s failed", sync_id)
        with SessionLocal() as db:
            sync = db.get(CorpusSync, sync_id)
            if sync:
                sync.status = "failed"
                sync.completed_at = datetime.now(timezone.utc)
                sync.errors_encountered += 1
                sync.error_details = str(exc)[:4000]
                db.commit()


def _persist_page(sync_id: int, papers, remaining_capacity: int) -> tuple[list[int], int]:
    new_document_ids: list[int] = []
    added_count = 0
    with SessionLocal() as db:
        sync = db.get(CorpusSync, sync_id)
        if sync is None:
            return [], 0
        sync.papers_discovered += len(papers)
        corpus_id = sync.corpus_id
        for paper in papers:
            if added_count >= remaining_capacity:
                break
            existing = db.execute(select(Documents).where(Documents.arxiv_id == paper.arxiv_id)).scalar_one_or_none()
            if existing is None:
                document = Documents(arxiv_id=paper.arxiv_id, title=paper.title, abstract=paper.abstract, authors=paper.authors, year_published=paper.submitted_at.year, url=paper.url, categories=", ".join(paper.categories), submitted_at=paper.submitted_at, arxiv_updated_at=paper.updated_at)
                db.add(document)
                db.flush()
                existing = document
                sync.papers_inserted += 1
                publish_entity_job(existing.id)
                publish_embedding_job(existing.id)
                sync.processing_jobs_enqueued += 2
                new_document_ids.append(existing.id)
            else:
                sync.existing_papers_skipped += 1
            membership = db.get(CorpusDocument, {"corpus_id": corpus_id, "document_id": existing.id})
            if membership is None:
                db.add(CorpusDocument(corpus_id=corpus_id, document_id=existing.id))
                added_count += 1
        db.commit()
    return new_document_ids, added_count


def _wait_for_embeddings(document_ids: list[int], timeout_seconds: int = 3600) -> None:
    """Wait for the batch embeddings before running one topic pass."""
    if not document_ids:
        return
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        with SessionLocal() as db:
            remaining = db.execute(
                select(Documents.id).where(
                    Documents.id.in_(document_ids),
                    Documents.embedded.is_(False),
                )
            ).scalars().first()
        if remaining is None:
            return
        time.sleep(5)
    raise TimeoutError("Timed out waiting for corpus embeddings")

