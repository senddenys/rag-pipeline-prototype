"""Unit tests for ingestion and chunking."""
from pathlib import Path

import pytest
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.ingest import chunk_documents
from app.config import CHUNK_SIZE, CHUNK_OVERLAP, CONTENT_DIR


def test_chunk_documents_splits_long_text():
    docs = [
        Document(page_content="A" * (CHUNK_SIZE + 200), metadata={"source": "test.md"}),
    ]
    chunks = chunk_documents(docs)
    assert len(chunks) >= 2
    total_len = sum(len(c.page_content) for c in chunks)
    assert total_len >= len(docs[0].page_content) - (CHUNK_OVERLAP * (len(chunks) - 1))


def test_chunk_documents_preserves_short_doc():
    short = Document(page_content="Short text.", metadata={"source": "a.md"})
    chunks = chunk_documents([short])
    assert len(chunks) == 1
    assert chunks[0].page_content == "Short text."
    assert chunks[0].metadata.get("source") == "a.md"


def test_chunk_documents_uses_separators():
    # Multiple paragraphs -> multiple chunks if over size
    content = "\n\n".join(["Paragraph " + str(i) for i in range(50)])
    docs = [Document(page_content=content, metadata={"source": "x.md"})]
    chunks = chunk_documents(docs)
    assert len(chunks) >= 1
    for c in chunks:
        assert c.page_content
        assert c.metadata.get("source") == "x.md"


@pytest.mark.skipif(not CONTENT_DIR.exists(), reason="content/ not present")
def test_content_dir_has_md_files():
    mds = list(CONTENT_DIR.rglob("*.md"))
    assert len(mds) >= 1, "At least one .md file expected in content/"
