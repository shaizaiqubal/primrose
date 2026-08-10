from google import genai
from pydantic import BaseModel
from sqlalchemy import case, select

from backend.app.config import (
    QDRANT_API_KEY,
    QDRANT_COLLECTION_NAME,
    QDRANT_PORT,
    QDRANT_URL,
    GEMINI_API_KEY
)

from backend.app.database import SessionLocal
from backend.app.models import Documents, Document_Topics, Topics
from backend.services.search import fetch_candidates
from qdrant_client import QdrantClient

client = QdrantClient(
    url=QDRANT_URL,
    port=QDRANT_PORT,
    api_key=QDRANT_API_KEY,
    check_compatibility=False
)

try:
    g_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as exc:
    g_client = None
    print("Gemini failed")

def get_unnamed_clusters():
    print("Fetching unnamed clusters...")
    with SessionLocal() as db:
        stmt = select(Topics.cluster_id).where(
            Topics.cluster_name.is_(None)
        )
        result = db.execute(stmt).scalars().all()

    print(f"Found {len(result)} unnamed clusters")
    return result

def get_ids(cluster):
    print(f"Looking up representative document IDs for cluster {cluster}...")

    with SessionLocal() as db:
        stmt = select(Topics.centroid).where(Topics.cluster_id==cluster)
        centroid = db.execute(stmt).scalar_one_or_none()

    if centroid is not None:
        result = client.query_points( #type:ignore
            collection_name=QDRANT_COLLECTION_NAME,
            query= list(centroid),
            limit=5,
            with_vectors=False,
            with_payload=False
        )

        ids = [point.id for point in result.points]
        print(f"Retrieved {len(ids)} representative document IDs for cluster {cluster}")
        return ids

    print(f"No centroid found for cluster {cluster}")
    return None

def get_clustername(ids):
    print(f"Generating cluster name from {len(ids or [])} representative papers...")
    papers = fetch_candidates(ids)
    papernames = [paper.title for paper in papers]
    interaction = g_client.interactions.create( # type: ignore
                model="gemini-3.1-flash-lite",
                input=f"""
                    Here are five representative papers from the same research cluster: {papernames}
                    """,
                system_instruction='''
                            You are a research taxonomy assistant.

                            You are given the titles of papers that are representative of a single research cluster.

                            Your task is to assign the cluster a concise, meaningful research topic name.

                            The topic name should:
                            - Describe the common research area or problem shared by the papers.
                            - Be specific enough to distinguish the topic from broader fields such as "Machine Learning", "Artificial Intelligence", or "Natural Language Processing".
                            - Prefer established research terminology when possible.
                            - Be short, ideally 3–7 words.
                            - Focus on the research topic, not the individual papers.
                            - Not mention that the papers were clustered.
                            - Not use numbering, quotation marks, or prefixes such as "Topic:".

                            Do not attempt to rank, summarize, or critique the papers.
                            Do not invent details that are unsupported by the papers.

                            Return only the topic name.
                                    '''
                
            )

    cluster_name = interaction.output_text
    print(f"Generated cluster name: {cluster_name}")
    return cluster_name

unnamed_clusters = get_unnamed_clusters()
for cluster in unnamed_clusters: #type:ignore
    print(f"Processing cluster {cluster}...")
    ids = get_ids(cluster)
    cluster_name = get_clustername(ids)

    with SessionLocal() as db:
        topic = db.get(Topics, cluster)

        if topic:
            topic.cluster_name = cluster_name
            db.commit()
            print(f"Saved cluster name for cluster {cluster}")
        else:
            print(f"Topic record not found for cluster {cluster}")

