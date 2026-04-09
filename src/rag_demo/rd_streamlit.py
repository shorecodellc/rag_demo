import streamlit as st
import asyncio

from rag_demo.rd_main import AgentDemo  # adjust import

st.set_page_config(page_title="Criminal Code RAG", layout="wide")

st.title("⚖️ Canadian Criminal Code RAG System")

# ---- Sidebar ----
st.sidebar.header("Settings")

api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# ---- Helper to run async ----
def run_async(coro):
    return asyncio.run(coro)

# ---- Init agent ----
@st.cache_resource
def load_agent(api_key):
    agent = AgentDemo(api_key)
    return agent

agent = None
if api_key:
    agent = load_agent(api_key)

# ---- Input ----
query = st.text_area("Enter your legal question:")

run_btn = st.button("Run")

# ---- Output containers ----
answer_box = st.empty()
log_box = st.expander("📜 Agent Logs", expanded=False)
docs_box = st.expander("📚 Retrieved Documents", expanded=False)

# ---- Execute ----
if run_btn and query and agent:
    with st.spinner("Running agent..."):

        graph = agent.build_graph()

        initial_state = {
            "question": query,
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

        answer_box.markdown("### 🧠 Answer")
        answer_box.write(result.get("answer", ""))

        # ---- Logs ----
        with log_box:
            for line in result.get("agent_log", []):
                st.text(line)

        # ---- Docs ----
        with docs_box:
            for i, doc in enumerate(result.get("retrieved_docs", []), 1):
                st.markdown(f"**[{i}] {doc.get('metadata').get('section')}**")
                st.write(doc.get("page_content", "")[:500])
                st.divider()