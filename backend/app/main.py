from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from backend.app.schemas import Document, DocumentResponse
from backend.app.database import SessionLocal, engine, Base 
from backend.app.models import Documents
from backend.services.vector_store import insert_embedding, get_related, query_documents
from backend.services.embed import embed_content
from backend.app.config import FRONTEND_URL
from sqlalchemy import select,case
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")
    yield

app = FastAPI(lifespan=lifespan)

origins = ["http://localhost:5173"]
if FRONTEND_URL:
    origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_document_or_404(db, id: int) -> Documents:
    stmt = select(Documents).where(Documents.id == id)
    result = db.execute(stmt).scalar_one_or_none()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return result

@app.get('/')
def root() -> dict:
    return {'message' : 'Primrose.S1 server is running!'}

@app.post('/documents', response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def post_documents(request : Document) -> Documents:
    with SessionLocal() as db:
        entry = Documents(
            title = request.title,
            abstract = request.abstract,
            authors = request.authors,
            year_published = request.year_published,
            url = request.url
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

@app.get('/documents', response_model=list[DocumentResponse])
def get_documents() -> list[Documents]:
    with SessionLocal() as db:
        stmt = select(Documents)
        result = list(db.execute(stmt).scalars().all())
        return result

@app.get("/documents/search", response_model=list[DocumentResponse])
def search_documents(query: str) -> list[Documents]: 
    query_embed = embed_content(abstract=query)
    try:
        related_ids = query_documents(query_embed)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Vector store query failed: {e}"
        )

    if not related_ids:
        return []
    
    with SessionLocal() as db:
        
        order = case(
            {doc_id: idx for idx, doc_id in enumerate(related_ids)},
            value=Documents.id
        )
        stmt = select(Documents).where(Documents.id.in_(related_ids)).order_by(order)
        related = list(db.execute(stmt).scalars().all())
        
        
    return related

@app.get('/documents/{id}', response_model=DocumentResponse)
def get_document(id: int) -> Documents:
    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        return result


@app.delete('/documents/{id}')
def delete_document(id: int) -> dict:
    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        db.delete(result)
        db.commit()
    return {'message': 'Document deleted successfully'}

@app.put('/documents/{id}', response_model=DocumentResponse)
def update_document(id: int, request: Document) -> Documents:
    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        result.title = request.title
        result.abstract = request.abstract
        result.authors = request.authors
        result.year_published = request.year_published
        result.url = request.url
        db.commit()
        db.refresh(result)
        return result

@app.post("/documents/{id}/embed")
def embed_document(id: int) -> dict:
    with SessionLocal() as db:
        result = _get_document_or_404(db, id)
        try:
            embedding = embed_content(title = result.title, abstract = result.abstract)
            insert_embedding(result, embedding)
            result.embedded = True
            db.commit()
            db.refresh(result)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Embedding failed: {e}"
            )
        
        return {'message': 'Embedded successfully'}
    

@app.get("/documents/{id}/related", response_model=list[DocumentResponse])
def get_related_documents(id: int) -> list[Documents]:
    try:
        related_ids = get_related(id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to retrieve related documents: {e}"
        )
    
    if not related_ids:
        return []
    with SessionLocal() as db:

        order = case(
            {doc_id: idx for idx, doc_id in enumerate(related_ids)},
            value=Documents.id
        )

        stmt = select(Documents).where(Documents.id.in_(related_ids)).order_by(order)
        related = list(db.execute(stmt).scalars().all())
        
    return related