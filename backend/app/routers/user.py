from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from backend.app.database import SessionLocal
from backend.app.models import User, Documents, Bookmark
from backend.app.schemas import UserResponse,DocumentResponse
from backend.app.routers.auth import get_current_user

router = APIRouter(prefix="/me", tags=["me"])

@router.get("", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_me(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user

@router.get("/uploads", response_model=list[DocumentResponse], status_code=status.HTTP_200_OK)
def get_user_uploads(
    current_user: User = Depends(get_current_user)
) -> list[Documents]:
    with SessionLocal() as db:
        stmt = select(Documents).where(
            Documents.uploaded_by == current_user.id
        )
        uploads = list(db.execute(stmt).scalars().all())
        return uploads

@router.get("/bookmarks", response_model=list[DocumentResponse], status_code=status.HTTP_200_OK)
def get_user_bookmarks(
    current_user: User = Depends(get_current_user)
) -> list[Documents]:

    with SessionLocal() as db:
        stmt = (
            select(Documents)
            .join(Bookmark, Bookmark.document_id == Documents.id)
            .where(Bookmark.user_id == current_user.id)
        )
        bookmarks = list(db.execute(stmt).scalars().all())
        return bookmarks

        