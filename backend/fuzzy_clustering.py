import numpy as np
import umap
import faiss
import pickle
import skfuzzy as fuzz
from sklearn.metrics.pairwise import cosine_similarity
from build_vector_db import SemanticSearch
from collections import Counter

search = SemanticSearch(tar_path="")

search.load("db")

num_vectors = search.index.ntotal

embeddings = search.index.reconstruct_n(0, num_vectors)
print(f"Extracted embeddings shape: {embeddings.shape}")

print("\nReducing dimensions with UMAP...")
reducer = umap.UMAP(n_neighbors=15, n_components=15, metric='cosine', random_state=42)
reduced_embeddings = reducer.fit_transform(embeddings)

# Fuzzy C - Means Clustering
print(f"\nApplying Fuzzy C-Means...")
data_for_fcm = reduced_embeddings.T

n_clusters = 20
m_fuzziness = 2.0

# Run FCM

cntr, u, u0, d, jm, p, fpc = fuzz.cluster.cmeans(
    data_for_fcm,
    c=n_clusters,
    m=m_fuzziness,
    error=0.005,
    maxiter=1000,
    init=None
)

print(f"FCM converged in {p} iterations. FPC: {fpc:.3f}")

# Transpose back so rows are documents, columns are cluster probabilities
document_memberships = u.T 
print(f"Final membership matrix shape: {document_memberships.shape}")

# Loading the saved documents
with open("db/documents.pkl", "rb") as f:
    documents = pickle.load(f)

true_labels = [doc['category'] for doc in documents]

print("\nMapping fuzzy clusters to true labels\n")
primary_cluster_assignments = np.argmax(document_memberships, axis=1)

cluster_names = {}

for cluster_id in range(20):
    # Docs where this cluster is primary assignment
    doc_indices_in_cluster = np.where(primary_cluster_assignments == cluster_id)[0]
    
    if len(doc_indices_in_cluster) == 0:
        cluster_names[cluster_id] == "Empty Cluster"
        continue

    labels_in_cluster = [true_labels[i] for i in doc_indices_in_cluster]

    label_counts = Counter(labels_in_cluster)
    most_common_label, count = label_counts.most_common(1)[0]

    percentage = count / len(doc_indices_in_cluster) * 100

    cluster_names[cluster_id] = most_common_label

print(cluster_names)

max_probabilities = np.max(document_memberships, axis=1)

# Find indices of docs that are shared across topics
fuzzy_threshold = 0.4
fuzzy_doc_indices = np.where(max_probabilities < fuzzy_threshold)[0]

print(f"Found {len(fuzzy_doc_indices)} highly fuzzy documents without a strong single topic.")
