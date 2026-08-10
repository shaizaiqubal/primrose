from collections import Counter
import numpy as np
from qdrant_client import QdrantClient
from sklearn.cluster import KMeans

from backend.app.config import (
    QDRANT_API_KEY,
    QDRANT_COLLECTION_NAME,
    QDRANT_PORT,
    QDRANT_URL,
)
from backend.app.database import SessionLocal
from backend.app.models import Document_Topics, Topics

print("TOPIC WORKER STARTED", flush=True)

client = QdrantClient(
    url=QDRANT_URL,
    port=QDRANT_PORT,
    api_key=QDRANT_API_KEY,
    check_compatibility=False
)

def get_embeddings():
    result = client.query_points(
        collection_name= QDRANT_COLLECTION_NAME,
        with_vectors= True,
        with_payload= False,
        limit=10000
    )

    vectors = [point.vector for point in result.points]
    ids = [point.id for point in result.points]

    return (vectors, ids)

def cluster_engine(embeddings):
    model = KMeans(n_clusters=100, init='k-means++',n_init=1,max_iter=300, random_state=42)

    model.fit(embeddings)

    return model

print("Fetching embeddings from Qdrant...")
(embeddings, doc_ids) = get_embeddings()
print(f"Retrieved {len(doc_ids)} embeddings")

embeddings = np.array(embeddings)
print("Clustering embeddings...")
kmeans = cluster_engine(embeddings)
print("Clustering complete")

labels = kmeans.labels_
centroids = kmeans.cluster_centers_
counts = Counter(labels)
print(f"Cluster counts: {dict(counts)}")

print("Writing topic summaries...")
with SessionLocal() as db:
    for c_id, c_centroid in enumerate(centroids):
        entry = Topics(
            cluster_id=int(c_id),
            cluster_name=None,
            paper_count=counts[c_id],
            centroid=c_centroid.tolist()
        )

        db.add(entry)

    db.commit()
print("Finished writing topic summaries")

print("Writing document-topic assignments...")
with SessionLocal() as db:
    for id,c_id in zip(doc_ids,labels):
        entry = Document_Topics(
            id = id,
            cluster_id = int(c_id)
        )

        db.add(entry)

    db.commit()
print("Finished writing document-topic assignments")

