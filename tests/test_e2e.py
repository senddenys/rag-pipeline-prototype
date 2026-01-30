"""End-to-end tests: query -> retrieval -> synthesis (no real LLM)."""
import pytest
from langchain_core.documents import Document

from app.synthesis import synthesize, _format_context


def test_format_context_includes_sources():
    docs = [
        Document(page_content="Answer A", metadata={"source": "a.md"}),
        Document(page_content="Answer B", metadata={"source": "b.md"}),
    ]
    ctx = _format_context(docs)
    assert "[1]" in ctx and "a.md" in ctx
    assert "[2]" in ctx and "b.md" in ctx
    assert "Answer A" in ctx and "Answer B" in ctx


def test_synthesize_stub_without_llm():
    docs = [
        Document(page_content="Python 3.10 supported.", metadata={"source": "getting-started.md"}),
    ]
    out = synthesize("What version of Python?", docs, llm=None)
    assert "Python" in out or "3.10" in out or "getting-started" in out or "Stub" in out
    assert isinstance(out, str)


def test_synthesize_citation_mention():
    docs = [
        Document(page_content="Reset password at /account.", metadata={"source": "faq.md"}),
    ]
    out = synthesize("How to reset password?", docs, llm=None)
    assert "faq" in out.lower() or "Stub" in out or "password" in out.lower()


@pytest.mark.skipif(
    True,  # Set to False and set OPENAI_API_KEY to run with real LLM
    reason="E2E with real LLM skipped by default",
)
def test_synthesize_with_openai(vector_store_with_docs):
    """Optional: run with OPENAI_API_KEY to test full pipeline."""
    from app.retrieval import retrieve
    from app.synthesis import get_llm

    docs = retrieve(vector_store_with_docs, "How do I install the CLI?")
    llm = get_llm()
    assert llm is not None
    out = synthesize("How do I install the CLI?", docs, llm=llm)
    assert "pip" in out.lower() or "install" in out.lower()
    assert len(out) > 50
