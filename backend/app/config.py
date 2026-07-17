from pathlib import Path
from dotenv import load_dotenv
import os

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
