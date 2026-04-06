# emantic Search

A full-stack semantic search application built over the 20 Newsgroups dataset. This project moves beyond simple keyword matching (BM25/TF-IDF) by utilizing dense vector embeddings, an in-memory semantic cache, and Fuzzy C-Means clustering to uncover the complex, overlapping semantic relationships between documents.


---

## Live Demos
* **Frontend UI (Vercel):** [https://semantic-search-newsgroups.vercel.app](https://semantic-search-newsgroups.vercel.app)

## Key Features

* **Dense Vector Search:** Uses `BAAI/bge-small-en-v1.5` to generate 384-dimensional embeddings, allowing users to search by *concept* rather than exact keyword.
* **Semantic Caching Layer:** Implements a secondary, lightweight in-memory FAISS index. If a new query is >92% semantically similar to a recent query, the API instantly returns the cached result, bypassing the main database.
* **Fuzzy Topic Modeling:** Uses UMAP dimensionality reduction and Scikit-Fuzzy (FCM) to cluster documents. Instead of hard-assigning a document to one category, the UI displays the semantic overlap (e.g., a document might be 60% `comp.sys.mac.hardware` and 40% `misc.forsale`).
* **Modern Monorepo:** Clean separation of concerns with a React/Vite frontend and a Dockerized FastAPI backend, communicating securely via standard REST protocols.

## Project Architecture


```text
SEMANTIC-SEARCH-NEWSGROUPS/
├── backend/                  # FastAPI & Machine Learning Logic
│   ├── db/                   # Pre-calculated FAISS index & Fuzzy matrices (Requires Git LFS)
│   ├── main.py               # FastAPI server and endpoints
│   ├── semantic_cache.py     # In-memory vector caching logic
│   ├── fuzzy_clustering.py   # UMAP & FCM implementation
│   ├── pyproject.toml        # Backend dependencies (managed via uv)
│   └── Dockerfile            # Container configuration for Hugging Face
│
└── frontend/                 # React UI
    ├── src/                  # React components, context, and hooks
    ├── public/               # Static assets
    ├── package.json          # Node dependencies
    └── vite.config.ts        # Vite configuration
```

## Setup
* Because the vector database relies on large .faiss and .npy files, Git LFS is required to clone the database successfully.
```
git clone https://github.com/suryavamsigara/semantic-search-newsgroups.git
cd semantic-search-newsgroups
git lfs pull
```

* The backend uses uv for lightning-fast dependency management.
```
cd backend
uv sync
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
* The API will be available at http://localhost:8000

```
cd frontend
npm install
npm run dev
```

## Deployment Strategy
* Backend (Hugging Face Spaces): The /backend directory is pushed as an isolated Git repository to Hugging Face. It runs inside a custom Docker container utilizing 16GB of RAM to hold the FAISS indices and UMAP models in memory.
* Frontend (Vercel): The main GitHub repository is linked to Vercel, with the Root Directory explicitly set to /frontend for automated Vite builds.
