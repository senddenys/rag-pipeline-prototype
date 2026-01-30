"""
Embedding generation and similarity search using ChromaDB.
"""
from __future__ import annotations

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

from app.config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL, TOP_K


def get_embedding_model() -> Embeddings:
    """Return embedding model (local HuggingFace by default)."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_vector_store(embedding: Embeddings, persist_directory: str = None):
    """Return Chroma vector store. If persist_directory given, use it; else in-memory."""
    persist_directory = persist_directory or str(CHROMA_PERSIST_DIR)
    return Chroma(
        collection_name="rag_docs",
        embedding_function=embedding,
        persist_directory=persist_directory,
    )


def retrieve(
    vector_store: Chroma,
    query: str,
    k: int = None,
) -> list[Document]:
    """Return top-k documents most similar to query."""
    k = k or TOP_K
    return vector_store.similarity_search(query, k=k)
