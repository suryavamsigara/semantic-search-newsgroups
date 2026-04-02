import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SemanticCache:
    def __init__(self, similarity_threshold=0.90):
        self.threshold = similarity_threshold
        self.store = {}
        self.stats = {"total_entries": 0, "hit_count": 0, "miss_count": 0}

    def check(self, query_emb, dominant_cluster):
        if dominant_cluster not in self.store or not self.store[dominant_cluster]:
            self.stats["miss_count"] += 1
            return None

        cached_items = self.store[dominant_cluster]
        cached_embs = np.vstack([item['embedding'] for item in cached_items])
        
        similarities = cosine_similarity(query_emb, cached_embs)[0]
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]

        if best_score >= self.threshold:
            self.stats["hit_count"] += 1
            return {
                "matched_query": cached_items[best_idx]["query"],
                "similarity_score": float(best_score),
                "result": cached_items[best_idx]["result"]
            }
        
        self.stats["miss_count"] += 1
        return None

    def put(self, query, query_emb, result, dominant_cluster):
        if dominant_cluster not in self.store:
            self.store[dominant_cluster] = []
        self.store[dominant_cluster].append({
            "query": query,
            "embedding": query_emb,
            "result": result
        })
        self.stats["total_entries"] += 1

    def get_stats(self):
        total = self.stats["hit_count"] + self.stats["miss_count"]
        hit_rate = self.stats["hit_count"] / total if total > 0 else 0.0
        return {
            "total_entries": self.stats["total_entries"],
            "hit_count": self.stats["hit_count"],
            "miss_count": self.stats["miss_count"],
            "hit_rate": round(hit_rate, 3)
        }

    def flush(self):
        self.store.clear()
        self.stats = {"total_entries": 0, "hit_count": 0, "miss_count": 0}
