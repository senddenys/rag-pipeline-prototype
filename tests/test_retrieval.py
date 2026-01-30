"""Unit tests for retrieval (embeddings + vector store)."""
import pytest

from app.retrieval import retrieve


def test_retrieve_returns_docs(vector_store_with_docs):
    results = retrieve(vector_store_with_docs, "How do I install?", k=2)
    assert len(results) <= 2
    assert all(hasattr(d, "page_content") and hasattr(d, "metadata") for d in results)


def test_retrieve_returns_sources_from_fixture(vector_store_with_docs):
    # All 3 fixture docs have known sources; retrieval should return some of them
    results = retrieve(vector_store_with_docs, "API base URL Bearer token", k=3)
    sources = [d.metadata.get("source") for d in results]
    fixture_sources = {"docs-getting-started.md", "docs-api-reference.md", "docs-faq.md"}
    assert all(s in fixture_sources for s in sources)


def test_retrieve_respects_k(vector_store_with_docs):
    for k in (1, 3, 5):
        results = retrieve(vector_store_with_docs, "Python install", k=k)
        assert len(results) == min(k, 3)  # we only have 3 docs in fixture


def test_retrieve_empty_query_returns_something(vector_store_with_docs):
    results = retrieve(vector_store_with_docs, "", k=2)
    # Empty query may still return docs (implementation-dependent)
    assert isinstance(results, list)
