"""Pytest fixtures for RAG tests."""
import tempfile
from pathlib import Path

import pytest
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.embeddings import FakeEmbeddings

from app.retrieval import get_vector_store


@pytest.fixture
def sample_docs():
    """Sample documents for testing chunking and retrieval."""
    return [
        Document(page_content="Python 3.10 and above are supported. Install with pip.", metadata={"source": "docs-getting-started.md"}),
        Document(page_content="The API base URL is https://api.company.com/v1. Use Bearer token.", metadata={"source": "docs-api-reference.md"}),
        Document(page_content="Reset password at https://app.company.com/account. Link expires in 24 hours.", metadata={"source": "docs-faq.md"}),
    ]


@pytest.fixture
def temp_chroma_dir():
    """Temporary directory for ChromaDB (no persist)."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def fake_embedding():
    """Deterministic fake embeddings for tests."""
    return FakeEmbeddings(size=64)


@pytest.fixture
def vector_store_with_docs(fake_embedding, temp_chroma_dir, sample_docs):
    """Chroma store with sample docs and fake embeddings."""
    store = get_vector_store(fake_embedding, persist_directory=temp_chroma_dir)
    store.add_documents(sample_docs)
    return store
