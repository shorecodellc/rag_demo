
"""
Enhanced RAG module for the Criminal Code of Canada.

Retrieval pipeline:
  1. BM25 sparse retrieval       (rank_bm25)
  2. FAISS dense retrieval       (OpenAI text-embedding-3-small)
  3. Reciprocal Rank Fusion      merges BM25 + FAISS ranked lists
  4. Cross-encoder re-ranking    Relevance scoring via Cross encoder
"""

from __future__ import annotations
import asyncio
import os
import re
import asyncio
import pickle
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi

from sentence_transformers import CrossEncoder
from langchain_core.documents.base import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.messages import SystemMessage, HumanMessage
import torch

from rag_demo.rd_document_ingestion import IngestionDemo
from rag_demo.rd_filepaths import Files
from rag_demo.rd_logging import set_logging

import numpy as np

class CrossEncoderReranker:
    """
    Applies cross-encoder re-ranking to improve semantic precision.

    Flow:
        1. Take retrieved docs
        2. Score (query, document) pairs jointly
        3. Sort by cross-encoder relevance
        4. Return top_k results
    """    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", top_k: int = 4) -> None:
        """
        Initialize cross-encoder reranker.

        Args:
            model_name (str):
                HuggingFace cross-encoder model identifier.
            top_k (int):
                Number of highest-scoring documents to return after reranking.
        """        
        self.model = CrossEncoder(model_name)
        self.top_k = top_k
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
        self.logger = set_logging(
            'cross_encoder',
            os.path.join(os.path.dirname(__file__), 'logging', 'la.log')
        )
        self.logger.info(f"Loading CrossEncoder on {device}")
    
        self.model = CrossEncoder(
                model_name,
                device=device
            )        

    async def arerank(self, query: str, docs: list) -> list[Document]:
        """
        Asynchronously rerank documents using cross-encoder scoring.

        Because CrossEncoder.predict() is synchronous and CPU/GPU bound,
        it is executed via asyncio.to_thread() to prevent event-loop blocking.

        Args:
            query (str):
                User query string.
            docs (list[Document]):
                Retrieved documents to rerank.

        Returns:
            list[Document]:
                Top-k reranked documents sorted by semantic relevance.
        """
        self.logger.debug(f"Re-ranking for {query}")
        if not docs:
            return []

        pairs = [(query, d.get("page_content", str())) for d in docs]

        # CrossEncoder is sync → run in thread
        scores = await asyncio.to_thread(self.model.predict, pairs)

        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
                
        self.logger.debug(f"Re-ranking finished for {query}")

        return [doc for doc, _ in ranked[: self.top_k]]

class RagDemo:
    def __init__(self, api_key: str):
        self.vectorstore = None       # faiss.IndexFlatIP (inner-product / cosine)
        self._bm25_index = None        # rank_bm25.BM25Okapi        
        self._tokenized_chunks: list[list[str]] = []
        self.embedder = self._get_embedder(api_key)
        
        self.reranker = CrossEncoderReranker()        
        
        self.filepaths = Files().get_files_list()
        self.logger = set_logging(__file__, self.filepaths[0])
        
        self.ingestor = IngestionDemo()
        if os.path.exists(os.path.join(self.filepaths[1], 'docs.pkl')):
            with open(os.path.join(self.filepaths[1], 'docs.pkl'), 'rb') as f:
                self._documents = pickle.load(f)
        else:            
            self._documents = self.ingestor.get_docs(self.filepaths[2])
            with open(os.path.join(self.filepaths[1], 'docs.pkl'), 'wb') as f:
                pickle.dump(self._documents, f)
        
        self._init_lock = asyncio.Lock()
        self._initialized = False
        self.logger.debug("Rag init complete")
        
    async def init(self):
        if self._initialized:
            return
    
        async with self._init_lock:
            if self._initialized:
                return
    
            await asyncio.gather(
                self.build_dense_index(),
                self.build_bm25_index(),
            )
    
            self._initialized = True
        
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace + lower tokeniser for BM25."""
        return re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()
    
    
    def _get_embedder(self, api_key: str):        
        _embedder = OpenAIEmbeddings(
            openai_api_key=api_key,
            model="text-embedding-3-small",
        )
        return _embedder
    
    def load_index(self):
        if os.path.exists(os.path.join(self.filepaths[1], 'index.faiss')):
            self.vectorstore = FAISS.load_local(
                self.filepaths[1],
                self.embedder,
                allow_dangerous_deserialization=True
            )
            self.logger.debug(f"[RAG] FAISS index loaded from disk")    
            return True
        return False
    
    def load_bm25_index(self):
        if os.path.exists(os.path.join(self.filepaths[1], 'bm25.pkl')):
            with open(os.path.join(self.filepaths[1], 'bm25.pkl'), 'rb') as f:
                self._bm25_index = pickle.load(
                    f,
                )
            self.logger.debug(f"[RAG] BM25 index loaded from disk")    
            return True
        return False    
    
    # ── index building ────────────────────────────────────────────────────────────
    
    async def build_dense_index(self):
        self.logger.debug("Loading FAISS index")
        if not self.load_index():
            
            self.vectorstore = await FAISS.afrom_documents(
                self._documents,
                self.embedder
            )
            self.logger.debug("Saving FAISS index")
            self.vectorstore.save_local(self.filepaths[1])
            self.logger.debug(f"[RAG] FAISS index built ({len(self._documents)} docs)")    
    
    async def build_bm25_index(self) -> None:
        """Build both the FAISS dense index and the BM25 sparse index."""
        if not self.load_bm25_index():
            # ---- extract text ----
            texts = [doc.page_content for doc in self._documents]            
            
            # ---- BM25 ----
            self._tokenized_chunks = [
                self._tokenize(t) for t in texts
            ]
            self._bm25_index = BM25Okapi(self._tokenized_chunks)
            
            with open(os.path.join(self.filepaths[1], 'bm25.pkl'), 'wb') as f:                
                pickle.dump(self._bm25_index, f)
        
            self.logger.debug(f"[RAG] BM25 index built ({len(self._documents)} docs)")   
    
    # ── retrieval stages ──────────────────────────────────────────────────────────
    
    def _bm25_ranked(self, query: str, k: int = 20) -> list[tuple[int, float]]:
        """Return (chunk_idx, score) sorted descending by BM25 score."""
        tokens = self._tokenize(query)
        scores = self._bm25_index.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return ranked[:k]
    
    
    async def _faiss_ranked(self, query: str, k: int = 20) -> list[tuple[Document, np.float32]]:
        return await self.vectorstore.asimilarity_search_with_score(query, k=k)
        
    def _reciprocal_rank_fusion(
        self, 
        bm25_list: list[tuple[int, float]], 
        faiss_list: list[tuple(Document, np.float32)],        
        k_rrf: int = 60,
    ) -> list[tuple[int, float]]:
        """
        Reciprocal Rank Fusion.
        Each list is [(document_idx, score), ...] sorted best-first.
        Returns a merged list sorted by RRF score descending.
        """
        rrf_scores: dict[str, tuple[float, Document]] = {}
        for bm_entry in bm25_list:
            doc = self._documents[bm_entry[0]]
            modifier = k_rrf + bm_entry[1]
            rrf_scores[doc.page_content] = (rrf_scores.get(doc.page_content, (0.0, 0.0))[0] + 1.0 / modifier, doc)
        for faiss_entry in faiss_list:
            doc = faiss_entry[0]
            modifier = k_rrf + float(faiss_entry[1])
            rrf_scores[doc.page_content] = (rrf_scores.get(doc.page_content, (0.0, 0.0))[0] + 1.0 / modifier, doc)
        return sorted(rrf_scores.items(), key=lambda x: x[1][0], reverse=True)
          
    async def retrieve(self, query: str, api_key: str, k: int = 5) -> list[dict]:
        """
        Full pipeline:
          BM25 + FAISS  →  Reciprocal Rank Fusion  →  LLM cross-encoder re-ranking
        Returns up to `k` re-ranked chunks.
        """
        if self.vectorstore is None or self._bm25_index is None:
            await self.init()        
        self.logger.debug("Rag retrieval initialized")
        candidate_pool = min(len(self._documents), max(k * 5, 20))
    
        # Stage 1 – independent ranked lists
        bm25_task = asyncio.to_thread(
            self._bm25_ranked, query, k=candidate_pool
        )
        faiss_task = self._faiss_ranked(query, k=candidate_pool)
    
        bm25_list, faiss_list = await asyncio.gather(
            bm25_task,
            faiss_task
        )
    
        # Stage 2 – Reciprocal Rank Fusion
        fused = self._reciprocal_rank_fusion(bm25_list, faiss_list, k_rrf=60)
    
        # Stage 3 – build candidate dicts (deduplicated, top 15 for re-ranking)
        rerank_candidates = [
            {**entry[1].model_dump(), "rrf_score": entry[0]}
            for _, entry in fused[:15]
        ]
    
        # Stage 4 – LLM cross-encoder re-ranking
        self.logger.debug("Rag retrieval complete")
        return await self.reranker.arerank(query, rerank_candidates)

if __name__ == '__main__':
    print(__file__)