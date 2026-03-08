### 1. The Vector Store: In-Memory NumPy
Instead of pulling in a heavy, dedicated vector database (like Chroma) this system uses **NumPy arrays** (`.npy`) loaded directly into memory. 
The cleaned corpus yields ~19,719 documents. When encoded with `all-MiniLM-L6-v2` (384 dimensions), the entire vector space occupies roughly ~30MB of RAM. Performing vectorized cosine similarity across a 30MB array via `numpy.dot` takes single-digit milliseconds. Introducing a dedicated vector database would add unnecessary network latency. This structure also seamlessly feeds into the downstream PCA and Gaussian Mixture Model pipelines.

### 2. Fuzzy Clustering: Temperature-Scaled GMM
We use a **Gaussian Mixture Model (GMM)** with a diagonal covariance matrix. GMMs treat clusters as overlapping probability distributions, meaning every document receives a continuous distribution profile rather than a rigid label.
Sentence-transformer embeddings push clusters far apart in the latent space, which can cause the GMM's softmax function to become overconfident (simulating hard clustering). We apply Temperature Scaling to the log-probabilities to relax the distribution, accurately revealing the semantic overlap and boundary cases.

### 3. The Semantic Cache
Similarity thrreshold is set to 0.90. It controls the system's tolerance for phrasing variations. If it is too low, it risks false positives, if it's too high, the cache becomes too strict.

## Quickstart (Local Execution)
This project uses `uv`
**(Note: The pre-computed embeddings and metadata are already included in the `vector_db/` directory, so you do not need to process the raw dataset to run the API.)**

**1. Clone the repository**
It also downloads the embeddings (.npy file) and metadata. (35 MiB)
```
git clone https://github.com/suryavamsigara/semantic-search-newsgroups
cd semantic-search-newsgroups
```

**2. Install Dependencies**
```
uv sync
```

**3. Run
```
uv run uvicorn main:app
```
or
```
uv run main.py
```

**4. Access the API
Open the interactive API documentation:
```
http://localhost:8000/docs
```
