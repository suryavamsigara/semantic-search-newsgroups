import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from clustering import run_fuzzy_clustering

def simulate_query(query_text, db_dir="./vector_db"):
    print(f"\n--- Initializing System & Processing Query ---")
    print(f"Query: '{query_text}'")
    
    # 1. Load the embeddings
    emb_path = f"{db_dir}/newsgroup_embeddings.npy"
    meta_path = f"{db_dir}/metadata.jsonl"
    
    try:
        corpus_embeddings = np.load(emb_path)
        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = [json.loads(line) for line in f]
    except FileNotFoundError:
        print("Error: Run build_vector_db.py first.")
        return

    # 2. Get the clustering models and optimal parameters dynamically from Part 2
    pca, gmm, best_k, temperature, distributions, bic_scores, k_candidates = run_fuzzy_clustering(db_dir)
    
    if pca is None or gmm is None:
        return

    # 3. Embed the new query
    print("\nEmbedding query...")
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    query_emb = encoder.encode([query_text])

    # 4. Find the Dominant Cluster using the temperature-scaled logic
    reduced_query = pca.transform(query_emb)
    log_probs = gmm._estimate_weighted_log_prob(reduced_query)
    scaled_log_probs = log_probs / temperature
    exp_log_probs = np.exp(scaled_log_probs - np.max(scaled_log_probs, axis=1, keepdims=True))
    query_distribution = exp_log_probs / np.sum(exp_log_probs, axis=1, keepdims=True)
    
    dominant_cluster = int(np.argmax(query_distribution[0]))

    # 5. Compute the "Miss" Result (Semantic Search across the entire corpus)
    similarities = cosine_similarity(query_emb, corpus_embeddings)[0]
    best_match_idx = np.argmax(similarities)
    best_document = metadata[best_match_idx]["text"]

    # 6. Format the output
    response = {
        "query": query_text,
        "cache_hit": False,
        "matched_query": None,
        "similarity_score": None,
        "result": best_document[:300] + "...",
        "dominant_cluster": dominant_cluster
    }

    print("\n=== FINAL RESPONSE ===")
    print(json.dumps(response, indent=4))
    
    return response

if __name__ == "__main__":
    test_phrase = "What is NASA space shuttle program?"
    simulate_query(test_phrase)