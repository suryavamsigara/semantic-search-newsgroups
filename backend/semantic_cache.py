import faiss
import numpy as np
import time

class SemanticCache:
    def __init__(self, model, dimension=384, threshold=0.85, max_size=1000):
        self.model = model
        self.threshold = threshold
        self.max_size = max_size

        self.cache_index = faiss.IndexFlatIP(dimension)

        self.cached_responses = []

    def check(self, query: str):
        """Returns cached response if a highly similar query exists."""

        if self.cache_index.ntotal == 0:
            return None
        
        # Embed the query
        query_vector = self.model.encode([query]).astype('float32')
        faiss.normalize_L2(query_vector)

        #  Search the cache
        distances, indices = self.cache_index.search(query_vector, k=1)

        similarity = distances[0][0]
        if similarity >= self.threshold:
            print(f"Semantic Cache Hit! (Similarity: {similarity:.3f})")
            cache_id = indices[0][0]
            return self.cached_responses[cache_id]
        
        return None
    
    def add(self, query: str, response: dict):
        """Adds a new query and its response to the cache"""
        if self.cache_index.ntotal >= self.max_size:
            print("Cache Full.. Flushing...")
            self.cache_index.reset()
            self.cached_responses.clear()

        query_vector = self.model.encode([query]).astype('float32')
        faiss.normalize_L2(query_vector)

        self.cache_index.add(query_vector)
        self.cached_responses.append(response)
