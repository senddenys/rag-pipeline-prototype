"""
Simple chat-style UI: single input and response area.
No auth, no session memory.
"""
import sys
from pathlib import Path

# Ensure project root is on path when run via: streamlit run app/chat_ui.py
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.config import CHROMA_PERSIST_DIR
from app.retrieval import get_embedding_model, get_vector_store, retrieve
from app.synthesis import synthesize


def _get_vector_store():
    if not CHROMA_PERSIST_DIR.exists():
        return None
    embedding = get_embedding_model()
    return get_vector_store(embedding, persist_directory=str(CHROMA_PERSIST_DIR))


def main():
    st.set_page_config(page_title="RAG Chat", page_icon="📚", layout="centered")
    st.title("RAG Pipeline — Chat")
    st.caption("Ask a question. Answers are based on the ingested content and cite sources.")

    vector_store = _get_vector_store()
    if vector_store is None:
        st.warning(
            "Vector store not found. Run ingestion first: `python -m app.ingest`"
        )
        st.stop()

    question = st.chat_input("Your question")
    if question:
        with st.spinner("Searching and generating..."):
            docs = retrieve(vector_store, question)
            answer = synthesize(question, docs)
        st.chat_message("user").write(question)
        st.chat_message("assistant").write(answer)


if __name__ == "__main__":
    main()
