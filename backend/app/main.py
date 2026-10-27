import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import FRONTEND_URL
from backend.app.routers import auth, corpora, documents, entities, recommendations, topics, user


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

origins = ["http://localhost:5173"]
if FRONTEND_URL:
    origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"message": "Primrose server is running!"}


app.include_router(documents.router)
app.include_router(entities.router)
app.include_router(topics.router)
app.include_router(recommendations.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(corpora.router)
