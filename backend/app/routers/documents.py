from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from backend.app.database import SessionLocal
from backend.app.models import Document_Entity, Documents, Entity, User, Bookmark
from backend.app.schemas import (
    Document,
    DocumentResponse,
    EntityResponse,
    RankedDocumentResponse,
)
from backend.services.embed import embed_content
from backend.services.reranker import RankedDocument
from backend.services.search import get_document_service, search
from backend.services.entities import (
    get_document_entity_ids,
)
from backend.services.vector_store import delete_embedding, insert_embedding
from backend.services.embedding_queue import publish_embedding_job, publish_entity_job
from backend.app.routers.auth import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])


def _get_document_or_404(db, id: int) -> Documents:
    stmt = select(Documents).where(Documents.id == id)
    result = db.execute(stmt).scalar_one_or_none()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return result


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def post_documents(
    request: Document,
    user: User = Depends(get_current_user)
    ) -> Documents:
    with SessionLocal() as db:
        entry = Documents(
            arxiv_id=request.arxiv_id,
            title=request.title,
            abstract=request.abstract,
            authors=request.authors,
            year_published=request.year_published,
            url=request.url,
            categories=request.categories,
            uploaded_by= user.id,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
    
    publish_entity_job(entry.id)
    publish_embedding_job(entry.id)
    return entry


@router.get("", response_model=list[DocumentResponse])
def get_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> list[Documents]:
    with SessionLocal() as db:
        stmt = (
            select(Documents)
            .order_by(Documents.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(db.execute(stmt).scalars().all())


@router.get("/search", response_model=list[RankedDocumentResponse])
def search_documents(
    query: str,
    entities: list[int] | None = Query(default=None),
) -> list[RankedDocument]:
    return search(query, entity_ids=entities)


@router.get("/{id}", response_model=DocumentResponse)
def get_document(id: int) -> Documents:
    return get_document_service(id)

@router.get("/{document_id}/entities", response_model=list[EntityResponse])
def get_document_entities(document_id: int) -> list[Entity]:
    with SessionLocal() as db:
        stmt = (
            select(Entity)
            .join(Document_Entity, Document_Entity.entity_id == Entity.id)
            .where(Document_Entity.document_id == document_id)
            .order_by(Entity.canonical_name, Entity.id)
        )
        return list(db.execute(stmt).scalars().all())


@router.delete("/{id}")
def delete_document(
    id: int,
    user: User = Depends(get_current_user)
    ) -> dict:

    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        if result.uploaded_by != user.id:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this document."
            )
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


@router.put("/{id}", response_model=DocumentResponse)
def update_document(
    id: int,
    request: Document,
    user: User = Depends(get_current_user)
    ) -> Documents:

    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        if result.uploaded_by != user.id:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this document."
            )
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

@router.post("/{document_id}/bookmark", status_code=status.HTTP_201_CREATED)
def add_bookmark(
    document_id: int,
    current_user: User = Depends(get_current_user),
) -> dict:
    with SessionLocal() as db:
        document = _get_document_or_404(db, document_id)

        existing_bookmark = db.execute(
            select(Bookmark).where(
                Bookmark.user_id == current_user.id,
                Bookmark.document_id == document.id,
            )
        ).scalar_one_or_none()

        if existing_bookmark:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document is already bookmarked.",
            )

        bookmark = Bookmark(
            user_id=current_user.id,
            document_id=document.id,
        )

        db.add(bookmark)
        db.commit()

    return {"message": "Document bookmarked successfully"}

@router.delete("/{document_id}/bookmark")
def remove_bookmark(
    document_id: int,
    current_user: User = Depends(get_current_user),
) -> dict:
    with SessionLocal() as db:
        document = _get_document_or_404(db, document_id)

        bookmark = db.execute(
            select(Bookmark).where(
                Bookmark.user_id == current_user.id,
                Bookmark.document_id == document.id,
            )
        ).scalar_one_or_none()

        if bookmark is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found.",
            )

        db.delete(bookmark)
        db.commit()

    return {"message": "Bookmark removed successfully"}


@router.post("/{id}/embed")
def embed_document(id: int) -> dict:
    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        try:
            embedding = embed_content(title=result.title, abstract=result.abstract)
            insert_embedding(
                result,
                embedding,
                entity_ids=get_document_entity_ids(result.id),
            )
            result.embedded = True
            db.commit()
            db.refresh(result)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Embedding failed: {exc}",
            )

        return {"message": "Embedded successfully"}
