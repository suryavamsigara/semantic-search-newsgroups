import json
import uvicorn
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from semantic_cache import SemanticCache
from clustering import run_fuzzy_clustering
from contextlib import asynccontextmanager

# Global variables for our models and data
encoder = None
pca_model = None
gmm_model = None
corpus_embeddings = None
corpus_metadata = None
TEMPERATURE = 7.0
cache = SemanticCache(similarity_threshold=0.90)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global encoder, pca_model, gmm_model, corpus_embeddings, corpus_metadata
    
    print("Loading Sentence Transformer...")
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("Loading embeddings...")
    corpus_embeddings = np.load("./vector_db/newsgroup_embeddings.npy")
    with open("./vector_db/metadata.jsonl", 'r', encoding='utf-8') as f:
        corpus_metadata = [json.loads(line) for line in f]
        
    print("Initializing Clustering Models...")
    pca_model, gmm_model, _, _, _, _, _ = run_fuzzy_clustering("./vector_db", temperature=TEMPERATURE)
    print("System Ready!")
    
    yield
    
    print("Shutting down Semantic Search API...")
    cache.flush()

app = FastAPI(title="Semantic Search", lifespan=lifespan)

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
def process_query(req: QueryRequest):
    """Embeds the query, checks the cache, and returns the result."""
    query_text = req.query
    query_emb = encoder.encode([query_text])
    
    # 1. Route the query to its dominant cluster
    reduced_query = pca_model.transform(query_emb)
    log_probs = gmm_model._estimate_weighted_log_prob(reduced_query)
    scaled_log_probs = log_probs / TEMPERATURE
    exp_log_probs = np.exp(scaled_log_probs - np.max(scaled_log_probs, axis=1, keepdims=True))
    distribution = exp_log_probs / np.sum(exp_log_probs, axis=1, keepdims=True)
    dominant_cluster = int(np.argmax(distribution[0]))

    # 2. Check the Semantic Cache
    cache_result = cache.check(query_emb, dominant_cluster)
    
    # 3. Cache Hit
    if cache_result:
        return {
            "query": query_text,
            "cache_hit": True,
            "matched_query": cache_result["matched_query"],
            "similarity_score": cache_result["similarity_score"],
            "result": cache_result["result"],
            "dominant_cluster": dominant_cluster
        }
        
    # 4. Cache Miss - Compute Result
    similarities = cosine_similarity(query_emb, corpus_embeddings)[0]
    best_match_idx = np.argmax(similarities)
    best_document = corpus_metadata[best_match_idx]["text"]
    best_score = float(similarities[best_match_idx])
    
    # Store in cache
    cache.put(query_text, query_emb, best_document, dominant_cluster)
    
    return {
        "query": query_text,
        "cache_hit": False,
        "matched_query": None,
        "similarity_score": best_score,
        "result": best_document,
        "dominant_cluster": dominant_cluster
    }

@app.get("/cache/stats")
def get_cache_stats():
    return cache.get_stats()

@app.delete("/cache")
def flush_cache():
    cache.flush()
    return {"message": "Cache flushed successfully"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)