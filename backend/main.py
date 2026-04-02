import uvicorn
from fastapi import FastAPI, Request, Depends
from pydantic import BaseModel
from contextlib import asynccontextmanager
from build_vector_db import SemanticSearch

class SearchRequest(BaseModel):
    query: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading saved index...")
    search = SemanticSearch(tar_path="")
    search.load("db")

    app.state.search = search

    print("✅ Ready!")
    yield

    print("Shutdown...")
    app.state.search = None

app = FastAPI(lifespan=lifespan)

def get_search(request: Request):
    return request.app.state.search

@app.post("/search")
async def search_api(body: SearchRequest, search=Depends(get_search)):
    return search.search(body.query)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)