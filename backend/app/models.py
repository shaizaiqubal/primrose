from sqlalchemy import DateTime, Text, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database import Base 
import datetime


class Documents(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    arxiv_id: Mapped[str | None] = mapped_column(unique=True, nullable=True)
    title: Mapped[str] = mapped_column()
    abstract: Mapped[str] = mapped_column()
    authors: Mapped[str | None] = mapped_column()
    year_published: Mapped[int | None] = mapped_column()
    url: Mapped[str | None] = mapped_column()
    categories: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at : Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, default=None)
    embedded : Mapped[bool] = mapped_column(default=False)


class Document_Topics(Base):
    __tablename__ = "document_topics"

    id: Mapped[int] = mapped_column(ForeignKey("documents.id"), primary_key=True, )
    cluster_id: Mapped[int] = mapped_column(ForeignKey("topics.cluster_id"))


class Topics(Base):
    __tablename__ = "topics"

    cluster_id: Mapped[int] = mapped_column(primary_key=True)
    cluster_name: Mapped[str | None] = mapped_column(nullable=True)
    paper_count: Mapped[int | None] = mapped_column()
    centroid: Mapped[list[float]] = mapped_column(JSON)


class User(Base):
    __tablename__="users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    email_verified: Mapped[bool] = mapped_column(
    default=False,
    nullable=False,
)


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
    )

    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
    )

    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id"), default=None, nullable=False)
    document_id : Mapped[int] = mapped_column(ForeignKey("documents.id"), default=None, nullable=False)
    created_at : Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "document_id",
            name="uq_bookmark_user_document",
        ),
    )