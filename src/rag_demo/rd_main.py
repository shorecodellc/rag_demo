#kevin fink
#kevin@shorecode.org
#Mon Apr  6 09:49:55 AM +07 2026
#

import sys
import json
import asyncio
import hashlib
from pydantic import BaseModel, Field
from typing import Literal, List

from rag_demo.rd_filepaths import Files
from rag_demo.rd_logging import set_logging

"""
LangGraph multi-agent pipeline for Criminal Code Q&A.

Agents:
  1. planner   – rewrites the user question into focused sub-queries
  2. retriever – runs FAISS retrieval for each sub-query
  3. synthesizer – generates the final answer with section citations
"""

from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage

from rag_demo.rd_rag import RagDemo

try:
    import redis.asyncio as redis
    import redis.exceptions.ConnectionError as RedisConnError
except ImportError:
    redis = None


class RedisCache:
    def __init__(self, url: str = "redis://localhost:6379/0"):
        self.enabled = False
        self.client = None

        if redis:
            try:
                self.client = redis.from_url(url)
                self.enabled = True
            except RedisConnError:
                self.enabled = False
                
    def _key(self, prefix: str, payload: dict) -> str:
        raw = json.dumps(payload, sort_keys=True)
        h = hashlib.sha256(raw.encode()).hexdigest()
        return f"{prefix}:{h}"

    async def get(self, key: str):
        if not self.enabled:
            return None
        try:            
            val = await self.client.get(key)
            return json.loads(val) if val else None
        except RedisConnError:
            return

    async def set(self, key: str, value: dict, ttl: int = 3600):
        try:            
            if not self.enabled:
                return
            await self.client.set(key, json.dumps(value), ex=ttl)
        except RedisConnError:
            return        
    
class AgentState(TypedDict):
    question: str
    api_key: str
    sub_queries: list[str]
    retrieved_docs: Annotated[list[dict], operator.add]
    answer: str
    agent_log: Annotated[list[str], operator.add]
    decision: str
    iteration: int
    review_feedback: str
    confidence: float
    
class PlannerOutput(BaseModel):
    sub_queries: List[str] = Field(description="2-3 search queries")

class SynthesizerOutput(BaseModel):
    answer: str

class ReviewerOutput(BaseModel):
    decision: Literal[
        "accept",
        "retry_retriever",
        "retry_planner",
        "retry_synthesizer",
    ]
    reason: str
    confidence: float = Field(
        description="Confidence score between 0 and 1"
    )

class AgentDemo:
    def __init__(self, api_key: str):
        files = Files()
        filepaths = files.get_files_list()
        log_fp = filepaths[0]
        
        self.logger = set_logging(__file__, log_fp)
        
        self.rag_system = RagDemo(api_key)        
        self.api_key = api_key
        self.cache = RedisCache()
    
    async def init(self):
        await self.rag_system.init()
        
    async def planner_node(self, state: AgentState) -> dict:
        payload = {
            "q": state["question"],
            "feedback": state.get("review_feedback", "")
        }
    
        key = self.cache._key("planner", payload)
        cached = await self.cache.get(key)
    
        if cached:
            return cached
        
        llm = ChatOpenAI(
            openai_api_key=state["api_key"],
            model="gpt-5-mini",
            temperature=0.2 if state.get("review_feedback") else 0,
        ).with_structured_output(PlannerOutput)
    
        feedback = state.get("review_feedback", "")
    
        prompt = (
            "Generate 2-3 precise legal search queries. Your queries should be limited to the Canadian Criminal Code\n\n"
            "If feedback is provided, improve the queries.\n\n"
            f"Question:\n{state['question']}\n\n"
            f"Feedback:\n{feedback}"
        )
    
        result: PlannerOutput = await llm.ainvoke(prompt)
    
        sub_queries = result.sub_queries[:3] or [state["question"]]
    
        output = {
            "sub_queries": sub_queries[:3],
            "agent_log": [f"[Planner] {sub_queries} (cached=False)"],
        }    
    
        await self.cache.set(key, output, ttl=3600)
    
        return output
    
    async def retriever_node(self, state: AgentState) -> dict:
        api_key = state["api_key"]
    
        tasks = []
        results = []
    
        for query in state["sub_queries"]:
            payload = {"query": query}
            key = self.cache._key("retrieval", payload)
    
            cached = await self.cache.get(key)
    
            if cached:
                results.append(cached)
            else:
                tasks.append((query, key))
    
        # run uncached queries in parallel
        if tasks:
            queries = [q for q, _ in tasks]
            fresh = await asyncio.gather(
                *[self.rag_system.retrieve(q, api_key, k=5) for q in queries]
            )
    
            for (q, key), docs in zip(tasks, fresh):
                await self.cache.set(key, docs, ttl=3600)
                results.append(docs)
    
        # flatten + dedupe
        seen = set()
        merged = []
    
        for docs in results:
            for d in docs:
                k = d.get("page_content", "")[:120]
                if k not in seen:
                    seen.add(k)
                    merged.append(d)

        return {
            "retrieved_docs": merged[:8],
            "agent_log": [f"[Retriever] {len(merged)} docs (cached mix)"],
        }
        
    async def synthesizer_node(self, state: AgentState) -> dict:
        context = "\n".join(
            f"{d.get('metadata', {}).get('section', "")}:{d.get('page_content', "")[:200]}"
            for d in state["retrieved_docs"]
        )
    
        payload = {
            "q": state["question"],
            "context": context,
            "feedback": state.get("review_feedback", "")
        }
    
        key = self.cache._key("synth", payload)
        cached = await self.cache.get(key)
    
        if cached:
            return cached
        
        llm = ChatOpenAI(
            openai_api_key=state["api_key"],
            model="gpt-5-mini",
            temperature=0.3 if state.get("review_feedback") else 0.2,
        ).with_structured_output(SynthesizerOutput)
    
        context = "\n\n---\n\n".join(
            f"{doc.get('metadata', {}).get('section', "")}\n{doc.get('page_content')}"
            for doc in state["retrieved_docs"]
        )
    
        feedback = state.get("review_feedback", "")
    
        prompt = (
            "Answer the question using the Criminal Code.\n\n"
            "It is crucial to preface your answer with: \n"
            "'The following text is not reliable legal advice. Please speak to an expert\n"
            "such as a lawyer or police officer to validate anything you read here."
            "Requirements:\n"
            "- Cite sections\n"
            "- Be accurate\n"
            "- Be complete\n\n"
            "If the question is not relevant to crime in Canada, answer with:\n"
            "I can only provide information about the Canadian Criminal Code\n\n"
            f"Question:\n{state['question']}\n\n"
            f"Context:\n{context}\n\n"
            f"Feedback:\n{feedback}"
        )
    
        result: SynthesizerOutput = await llm.ainvoke(prompt)
    
        output = {
            "answer": result.answer,
            "agent_log": ["[Synthesizer] cached=False"],
        }    
    
        await self.cache.set(key, output, ttl=3600)
    
        return output
    
    async def reviewer_node(self, state: AgentState) -> dict:
        payload = {
            "q": state["question"],
            "answer": state["answer"]
        }
    
        key = self.cache._key("review", payload)
        cached = await self.cache.get(key)
    
        if cached:
            return cached
        
        llm = ChatOpenAI(
            openai_api_key=state["api_key"],
            model="gpt-5-mini",
            temperature=0,
        ).with_structured_output(ReviewerOutput)
    
        context_preview = "\n\n".join(
            doc.get('page_content', "")[:300] for doc in state["retrieved_docs"][:3]
        )
    
        prompt = (
            "Evaluate answer quality.\n\n"
            "Criteria:\n"
            "- factual correctness\n"
            "- completeness\n"
            "- proper citations\n\n"
            "If the answer is specifically 'I can only provide information about the Canadian Criminal Code:\n'"
            "Reply with 1.0 confidence and accept with a reason of 'Question is for other juridictions'."
            "Return decision and confidence.\n\n"
            f"Question:\n{state['question']}\n\n"
            f"Answer:\n{state['answer']}\n\n"
            f"Context:\n{context_preview}"
        )
    
        result: ReviewerOutput = await llm.ainvoke(prompt)
        
        output = {
            "decision": result.decision,
            "review_feedback": result.reason,
            "confidence": result.confidence,
            "iteration": state.get("iteration", 0) + 1,
            "agent_log": [
                f"[Reviewer] {result.decision} ({result.confidence:.2f})"
            ],
        }
    
        await self.cache.set(key, output, ttl=1800)
    
        return output
    
    def route_after_review(self, state: AgentState) -> str:
        if state["iteration"] > 3:
            return "end"
    
        if state.get("confidence", 0) > 0.85:
            return "accept"
    
        return state.get("decision", "end")
    
    def build_graph(self,) -> StateGraph:
        graph = StateGraph(AgentState)
    
        graph.add_node("planner", self.planner_node)
        graph.add_node("retriever", self.retriever_node)
        graph.add_node("synthesizer", self.synthesizer_node)
        graph.add_node("reviewer", self.reviewer_node)
    
        graph.set_entry_point("planner")
        graph.add_edge("planner", "retriever")
        graph.add_edge("retriever", "synthesizer")
        graph.add_edge("synthesizer", "reviewer")
        
        graph.add_conditional_edges(
            "reviewer",
            self.route_after_review,
            {
                "accept": END,
                "retry_retriever": "retriever",
                "retry_planner": "planner",
                "retry_synthesizer": "synthesizer",
                "end": END,
            },
        )    
    
        return graph.compile()            
    
    def get_graph():
        if _compiled_graph is None:
            _compiled_graph = build_graph()
        return _compiled_graph

if __name__ == '__main__':
    def run_async(coro):
        return asyncio.run(coro)
    api_key = input("Enter OpenAI api key: ")
    agent = AgentDemo(api_key)
    graph = agent.build_graph()

    initial_state = {
        "question": 'What are the consequences of stealing 5 donuts and 2 pieces of wood',
        "api_key": api_key,
        "sub_queries": [],
        "retrieved_docs": [],
        "answer": "",
        "agent_log": [],
        "decision": "",
        "iteration": 0,
        "review_feedback": "",
        "confidence": 0.0,
    }

    result = run_async(graph.ainvoke(initial_state))

