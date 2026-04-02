import numpy as np
import json
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA

def run_fuzzy_clustering(emb_dir, temperature=6.0):
    print("Loading embeddings and metadata...")
    emb_path = f"{emb_dir}/newsgroup_embeddings.npy"
    meta_path = f"{emb_dir}/metadata.jsonl"
    
    try:
        embeddings = np.load(emb_path)
        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = [json.loads(line) for line in f]
    except FileNotFoundError:
        print("Error: Run build_vecror_db.py first.")
        return None, None, None, None, None, None, None

    print("Applying PCA (20 components)...")
    pca = PCA(n_components=20, random_state=42)
    reduced_embeddings = pca.fit_transform(embeddings)

    print("Testing cluster counts using BIC...")
    k_candidates = [10, 15, 20, 25, 30]
    bic_scores = []  # to track the scores for the plot
    
    best_k = 10
    best_bic = float('inf')
    
    for k in k_candidates:
        gmm_test = GaussianMixture(n_components=k, covariance_type='diag', random_state=42)
        gmm_test.fit(reduced_embeddings)
        current_bic = gmm_test.bic(reduced_embeddings)
        bic_scores.append(current_bic) # Store the score
        
        print(f"k={k} | BIC Score: {current_bic:.2f}")
        
        if current_bic < best_bic:
            best_bic = current_bic
            best_k = k
            
    print(f"Optimal cluster count found: k={best_k} (Lowest BIC)")

    print(f"\nFitting final GMM with {best_k} clusters...")
    gmm = GaussianMixture(n_components=best_k, covariance_type='diag', random_state=42)
    gmm.fit(reduced_embeddings)
    
    # Apply Temperature Scaling to reveal semantic overlaps
    log_probs = gmm._estimate_weighted_log_prob(reduced_embeddings)
    scaled_log_probs = log_probs / temperature
    exp_log_probs = np.exp(scaled_log_probs - np.max(scaled_log_probs, axis=1, keepdims=True))
    distributions = exp_log_probs / np.sum(exp_log_probs, axis=1, keepdims=True)

    print("\n--- Semantic Structure Analysis ---")
    max_probs = np.max(distributions, axis=1)
    sorted_probs = np.sort(distributions, axis=1)
    
    core_indices = np.where(max_probs > 0.60)[0]
    margin = sorted_probs[:, -1] - sorted_probs[:, -2]
    boundary_indices = np.where((margin < 0.15) & (max_probs <= 0.60))[0]
    uncertain_indices = np.where(max_probs < 0.20)[0]

    print(f"Total Documents: {len(embeddings)}")
    print(f"Core Documents: {len(core_indices)}")
    print(f"Boundary Documents: {len(boundary_indices)}")
    print(f"Highly Uncertain Documents: {len(uncertain_indices)}\n")

    if len(boundary_indices) > 0:
        example_idx = boundary_indices[0]
        top_2_clusters = np.argsort(distributions[example_idx])[-2:][::-1]
        
        print("--- Example Boundary Case ---")
        print(f"Original Category: {metadata[example_idx]['category']}")
        print(f"Text Snippet: {metadata[example_idx]['text'][:400]}...")
        print("Cluster Distribution:")
        print(f"  -> Cluster {top_2_clusters[0]}: {distributions[example_idx, top_2_clusters[0]]:.3f}")
        print(f"  -> Cluster {top_2_clusters[1]}: {distributions[example_idx, top_2_clusters[1]]:.3f}")

    return pca, gmm, best_k, temperature, distributions, bic_scores, k_candidates

if __name__ == "__main__":
    run_fuzzy_clustering("./vector_db")