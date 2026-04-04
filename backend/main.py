import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from build_vector_db import SemanticSearch
from fuzzy_clustering import FuzzyClustering

class SearchRequest(BaseModel):
    query: str

class DocRequest(BaseModel):
    doc: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading saved index...")
    search = SemanticSearch(tar_path="")
    search.load("db")

    clustering = FuzzyClustering(search=search)

    if not clustering.load("db"):
        print("Calculating FCM clusters (this will take a minute)...")
        clustering.run_fcm()
        clustering.save("db")

    app.state.search = search
    app.state.clustering = clustering

    print("✅ Ready!")
    yield

    print("Shutdown...")
    app.state.search = None

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_search(request: Request):
    return request.app.state.search

def get_clustering(request: Request):
    return request.app.state.clustering

@app.post("/search")
async def search_api(body: SearchRequest, search=Depends(get_search)):
    return search.search(body.query)

@app.get("/document/{filename}")
async def get_document(filename: str, search=Depends(get_search)):
    doc = next((d for d in search.documents if d.get("filename") == filename), None)

    if doc is None:
        return {"error": "Document not found"}
    return doc

@app.post("/categories")
async def get_categories(doc: DocRequest, search=Depends(get_search), clustering=Depends(get_clustering)):
    documents = search.documents
    index = next((i for i, d in enumerate(documents) if d.get("filename") == doc.doc), None)

    if index is None:
        return {"error": f"Document {doc.doc} not found."}
    return clustering.find_categories(index)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)