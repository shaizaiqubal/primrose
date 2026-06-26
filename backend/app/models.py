from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database import Base # type: ignore
import datetime

# class Base(DeclarativeBase):
#     pass

class Documents(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    abstract: Mapped[str] = mapped_column()
    authors: Mapped[str | None] = mapped_column()
    year_published: Mapped[int | None] = mapped_column()
    url: Mapped[str | None] = mapped_column()
    created_at : Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    embedded : Mapped[bool] = mapped_column(default=False)

