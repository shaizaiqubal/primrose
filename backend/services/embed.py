from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_content(title="", abstract=""):
    content = title + "\n\n" + abstract
    embedding = model.encode(content)
    return embedding