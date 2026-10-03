from fastapi import APIRouter

from backend.app.schemas import DocumentResponse, TopicResponse
from backend.services.topics import get_topic, get_topic_papers, get_topics


router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicResponse])
def topics():
    return get_topics()


@router.get("/{topic_id}", response_model=TopicResponse)
def topic(topic_id: int):
    return get_topic(topic_id)


@router.get("/{topic_id}/papers", response_model=list[DocumentResponse])
def topic_papers(topic_id: int):
    return get_topic_papers(topic_id)