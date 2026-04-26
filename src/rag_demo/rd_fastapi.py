import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from rag_demo.rd_rag import RagDemo
from rag_demo.rd_codegen import CodeGenerator, CodegenRequest, CodegenResponse, _strip_fences, _extract_node_names
from rag_demo.routes.rd_horses import router as horses_router

app = FastAPI(title="Criminal Code RAG API (Retrieval Only)")
app.include_router(horses_router)


# ---- Request / Response Models ----
class QueryRequest(BaseModel):
    query: str
    api_key: str


class QueryResponse(BaseModel):
    retrieved_docs: list
        
# ---- CORS CONFIG ----
origins = [
    "http://localhost:9000",
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


# ---- Codegen instance ----
_codegen = CodeGenerator()


# ---- LangGraph generator endpoint (one-shot) ----
@app.post("/codegen", response_model=CodegenResponse)
async def generate_agent(request: CodegenRequest):
    if not request.description:
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    try:
        return await _codegen.generate(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- LangGraph generator endpoint (streaming SSE) ----
@app.post("/codegen/stream")
async def stream_agent(request: CodegenRequest):
    if not request.description:
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    accumulated: list[str] = []

    async def event_generator():
        try:
            async for token in _codegen.stream_tokens(request):
                accumulated.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Send final node_names after streaming completes
            full_code = _strip_fences("".join(accumulated))
            node_names = _extract_node_names(full_code)
            yield f"data: {json.dumps({'done': True, 'node_names': node_names})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")