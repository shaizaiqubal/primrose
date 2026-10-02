import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models import Documents
from backend.app.schemas import Document, DocumentResponse, RankedDocumentResponse
from backend.services.embed import embed_content
from backend.services.queue_docs import queue_documents
from backend.services.reranker import RankedDocument
from backend.services.search import get_document_service, search
from backend.services.vector_store import delete_embedding, insert_embedding


router = APIRouter()


def _get_document_or_404(db, id: int) -> Documents:
    stmt = select(Documents).where(Documents.id == id)
    result = db.execute(stmt).scalar_one_or_none()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return result


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def post_documents(request: Document) -> Documents:
    with SessionLocal() as db:
        entry = Documents(
            arxiv_id=request.arxiv_id,
            title=request.title,
            abstract=request.abstract,
            authors=request.authors,
            year_published=request.year_published,
            url=request.url,
            categories=request.categories,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        db.close()

    message_id = queue_documents(entry)
    logging.info("Published message %s", message_id)
    return entry


@router.get("/documents", response_model=list[DocumentResponse])
def get_documents() -> list[Documents]:
    with SessionLocal() as db:
        stmt = select(Documents).order_by(Documents.id).limit(50)
        return list(db.execute(stmt).scalars().all())


@router.get("/documents/search", response_model=list[RankedDocumentResponse])
def search_documents(query: str) -> list[RankedDocument]:
    return search(query)


@router.get("/documents/{id}", response_model=DocumentResponse)
def get_document(id: int) -> Documents:
    return get_document_service(id)


@router.delete("/documents/{id}")
def delete_document(id: int) -> dict:
    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        try:
            delete_embedding(result.id)
            db.delete(result)
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Delete failed: {exc}",
            )
    return {"message": "Document deleted successfully"}


@router.put("/documents/{id}", response_model=DocumentResponse)
def update_document(id: int, request: Document) -> Documents:
    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        result.title = request.title
        result.abstract = request.abstract
        result.authors = request.authors
        result.year_published = request.year_published
        result.url = request.url
        result.categories = request.categories
        result.arxiv_id = request.arxiv_id
        db.commit()
        db.refresh(result)
        return result


@router.post("/documents/{id}/embed")
def embed_document(id: int) -> dict:
    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        try:
            embedding = embed_content(title=result.title, abstract=result.abstract)
            insert_embedding(result, embedding)
            result.embedded = True
            db.commit()
            db.refresh(result)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Embedding failed: {exc}",
            )

        return {"message": "Embedded successfully"}