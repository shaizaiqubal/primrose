import logging
import base64
import json
from backend.app.database import SessionLocal
from backend.app.models import Documents
from backend.services.embed import embed_content
from backend.services.vector_store import insert_embedding
from sqlalchemy import select
from fastapi import FastAPI, Request

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

def get_doc_id(pubsub_message: dict) -> int:
    data = pubsub_message["message"]["data"]
    decoded = base64.b64decode(data).decode("utf-8")
    payload = json.loads(decoded)
    return payload["document_id"]

def process_document(document_id):
    logging.info(f"Processing document {document_id}")
    with SessionLocal() as db:
        stmt = select(Documents).where(Documents.id == document_id)
        doc = db.execute(stmt).scalar_one_or_none()
        if doc is None:
            logging.error(f"Document {document_id} not found")
            return
        if doc.embedded:
            logging.info(f"Document {document_id} already embedded")
            return
        embedding = embed_content(doc.title,doc.abstract)
        insert_embedding(doc,embedding)
        doc.embedded = True
        db.commit()
        db.refresh(doc)
    logging.info(f"Completed document {document_id}")


@app.post('/')
async def process(request: Request) -> dict:
    pubsub_message = await request.json()
    logging.info(f"RAW REQUEST: {pubsub_message}")
    doc_id = get_doc_id(pubsub_message)
    try:
        process_document(doc_id)
    except Exception:
        logging.exception(f"Failed processing {doc_id}")
        raise
    return {'status' : 'ok'}
