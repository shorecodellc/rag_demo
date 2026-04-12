from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_demo.rd_rag import RagDemo

app = FastAPI(title="Criminal Code RAG API (Retrieval Only)")


# ---- Request / Response Models ----
class QueryRequest(BaseModel):
    query: str
    api_key: str


class QueryResponse(BaseModel):
    retrieved_docs: list
        
# ---- CORS CONFIG ----
origins = [
    #"http://localhost:9000"
    "https://ragdemo.shorecode.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # or ["POST"]
    allow_headers=["*"],
)

# ---- Cache RAG instances ----
_rag_instances = {}


def get_rag(api_key: str) -> RagDemo:
    if api_key not in _rag_instances:
        _rag_instances[api_key] = RagDemo(api_key)
    return _rag_instances[api_key]


# ---- Health check ----
@app.get("/")
def root():
    return {"status": "ok", "message": "RAG Retrieval API running"}


# ---- Retrieval endpoint ----
@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        rag = get_rag(request.api_key)

        docs = await rag.retrieve(
            query=request.query,
            k=5
        )

        clean_docs = [
            {
                "page_content": d.get("page_content", ""),
                "metadata": d.get("metadata", {}),
                "score": d.get("rrf_score", None),
            }
            for d in docs
        ]

        return QueryResponse(retrieved_docs=clean_docs)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))