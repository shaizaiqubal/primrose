from sqlalchemy import DateTime, Text, ForeignKey, String, JSON, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import ARRAY
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
    submitted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arxiv_updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CorpusConfig(Base):
    __tablename__ = "corpus_configs"
    __table_args__ = (UniqueConstraint("user_id", name="uq_corpus_config_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="arxiv")
    categories: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    last_synced: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CorpusDocument(Base):
    __tablename__ = "corpus_documents"

    corpus_id: Mapped[int] = mapped_column(ForeignKey("corpus_configs.id", ondelete="CASCADE"), primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    added_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CorpusSync(Base):
    __tablename__ = "corpus_syncs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    corpus_id: Mapped[int] = mapped_column(ForeignKey("corpus_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    historical_backfill: Mapped[bool] = mapped_column(nullable=False, default=False)
    papers_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    papers_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    existing_papers_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processing_jobs_enqueued: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors_encountered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    upper_cutoff: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


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


class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (UniqueConstraint("canonical_name", "type"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column()
    type: Mapped[str] = mapped_column()
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)



class Document_Entity(Base):
    __tablename__ = "document_entities"

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    entity_id: Mapped[int] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    confidence: Mapped[float] = mapped_column(default=1.0)
    extractor_version: Mapped[str] = mapped_column()
