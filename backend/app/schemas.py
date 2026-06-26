from pydantic import BaseModel
from datetime import datetime

class Document(BaseModel):
    title : str
    abstract : str
    authors: str | None
    year_published: int | None
    url: str | None

class DocumentResponse(BaseModel):
    id: int
    title: str
    abstract: str
    authors: str | None
    year_published: int | None
    url: str | None
    created_at: datetime
    embedded: bool

    model_config = {
        "from_attributes": True
    }