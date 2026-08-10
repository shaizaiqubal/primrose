from sqlalchemy import DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database import Base # type: ignore
import datetime

# class Base(DeclarativeBase):
#     pass

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
