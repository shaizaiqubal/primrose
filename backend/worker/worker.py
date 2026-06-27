import logging
from backend.app.database import SessionLocal
from backend.app.models import Documents
from backend.services.embed import embed_content
from backend.services.vector_store import insert_embedding
from sqlalchemy import select
from time import sleep

FAST_SLEEP = 2  # seconds
SLOW_SLEEP = 30  # seconds

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s')

def get_unembedded_documents():
    with SessionLocal() as db:
        stmt = select(Documents).where(Documents.embedded==False).limit(20)
        result = db.execute(stmt).scalars().all()
        logging.info(f"Found {len(result)} unembedded documents")
        return [doc.id for doc in result]

def process_document(document_id):
    logging.info(f"Processing document {document_id}")
    with SessionLocal() as db:
        stmt = select(Documents).where(Documents.id == document_id)
        doc = db.execute(stmt).scalar_one()
        embedding = embed_content(doc.title,doc.abstract)
        insert_embedding(doc,embedding)
        doc.embedded = True
        db.commit()
        db.refresh(doc)
    logging.info(f"Completed document {document_id}")

def process_pending_documents():
    doc_ids = get_unembedded_documents()
    processed = 0
    for doc_id in doc_ids:
        try:
            process_document(doc_id)
            processed += 1
        except Exception as e:
            logging.error(f"Error processing doc {doc_id}: {e}", exc_info=True)
    return processed

if __name__ == "__main__":
    logging.info("Worker started (fast poll: 2s, idle poll: 30s)")
    while True:
        logging.info("Checking for pending documents...")

        processed = process_pending_documents()

        if processed > 0:
            logging.info(
                f"Processed {processed} documents. Sleeping {FAST_SLEEP}s."
            )
            sleep(FAST_SLEEP)
        else:
            logging.info(
                f"No pending documents. Sleeping {SLOW_SLEEP}s."
            )
            sleep(SLOW_SLEEP)