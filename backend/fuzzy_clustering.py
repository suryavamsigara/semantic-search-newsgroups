import umap
import skfuzzy as fuzz
import numpy as np
from build_vector_db import SemanticSearch
from collections import Counter

class FuzzyClustering:
    def __init__(self, search: SemanticSearch):
        self.index = search.index
        self.documents = search.documents
        self.document_memberships = None
        self.cluster_names = {}
    
    def run_fcm(self):
        if self.index is None:
            print("Index is none.")
            return
        
        num_vectors = self.index.ntotal
        embeddings = self.index.reconstruct_n(0, num_vectors)
        print(f"Extracted embeddings shape: {embeddings.shape}")
        
        print("\nReducing dimensions with UMAP...")
        reducer = umap.UMAP(n_neighbors=30, n_components=15, min_dist=0.0, metric='cosine', random_state=42)
        reduced_embeddings = reducer.fit_transform(embeddings)

        # Fuzzy C-Means Clustering
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
        self.document_memberships = u.T 
        print(f"Final membership matrix shape: {self.document_memberships.shape}")

        max_probabilities = np.max(self.document_memberships, axis=1)

        # Find indices of docs that are shared across different labels
        fuzzy_threshold = 0.4
        fuzzy_doc_indices = np.where(max_probabilities < fuzzy_threshold)[0]
        print(f"Found {len(fuzzy_doc_indices)} highly fuzzy documents without a strong single topic.")


        true_labels = [doc['category'] for doc in self.documents]

        print("\nMapping fuzzy clusters to true labels\n")

        primary_cluster_assignments = np.argmax(self.document_memberships, axis=1)

        for cluster_id in range(20):
            doc_indices_in_cluster = np.where(primary_cluster_assignments == cluster_id)[0]

            if len(doc_indices_in_cluster) == 0:
                self.cluster_names[cluster_id] = "Empty Cluster"
                continue

            labels_in_cluster = [true_labels[i] for i in doc_indices_in_cluster]

            label_counts = Counter(labels_in_cluster)
            most_common_label, count = label_counts.most_common(1)[0]

            self.cluster_names[cluster_id] = most_common_label
        print("Finished")
    
    def find_categories(self, index: int):
        document_array = self.document_memberships[index]

        top_3_cluster_indices = np.argsort(document_array)[::-1][:3].flatten()
        return {
            "clusters": [self.cluster_names.get(c) for c in top_3_cluster_indices]
        }


if __name__=="__main__":
    search = SemanticSearch(tar_path="")
    search.load("db")
    clustering = FuzzyClustering(search)
    clustering.run_fcm()

