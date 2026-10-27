from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import date

REPO_ROOT = Path(__file__).resolve().parents[2]

if os.getenv("TESTING") == "1":
    load_dotenv(REPO_ROOT / ".env.test")
else:
    load_dotenv(REPO_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION_NAME",
    "document_vectors",
)
HF_TOKEN = os.getenv("HF_TOKEN")
FRONTEND_URL = os.getenv("FRONTEND_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_HOST=os.getenv("REDIS_HOST", "cache")
REDIS_PORT=int(os.getenv("REDIS_PORT", 6379))
REDIS_USER=os.getenv("REDIS_USER")
REDIS_PASSWORD=os.getenv("REDIS_PASSWORD")
JWT_SECRET=os.getenv("JWT_SECRET")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

ARXIV_API_URL = os.getenv("ARXIV_API_URL", "https://export.arxiv.org/api/query")
ARXIV_API_TIMEOUT_SECONDS = float(os.getenv("ARXIV_API_TIMEOUT_SECONDS", "30"))
ARXIV_REQUEST_INTERVAL_SECONDS = float(os.getenv("ARXIV_REQUEST_INTERVAL_SECONDS", "3"))
ARXIV_PAGE_SIZE = int(os.getenv("ARXIV_PAGE_SIZE", "100"))
ARXIV_DEFAULT_START_DATE = date.fromisoformat(os.getenv("ARXIV_DEFAULT_START_DATE", "1990-01-01"))
