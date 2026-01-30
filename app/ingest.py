"""
Ingestion and chunking of content.
Loads Markdown (and optionally PDF) from content/, chunks, and builds ChromaDB.
"""
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHROMA_PERSIST_DIR, CONTENT_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from app.retrieval import get_embedding_model, get_vector_store


def _get_loader():
    """Load .md and .txt from content/."""
    return DirectoryLoader(
        str(CONTENT_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )


def chunk_documents(documents):
    """Split documents into chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)


def run_ingest():
    """Load content, chunk, embed, and persist to ChromaDB."""
    if not CONTENT_DIR.exists():
        raise FileNotFoundError(f"Content directory not found: {CONTENT_DIR}")

    loader = _get_loader()
    documents = loader.load()
    if not documents:
        raise ValueError(f"No documents found in {CONTENT_DIR}")

    chunks = chunk_documents(documents)
    print(f"Loaded {len(documents)} documents, split into {len(chunks)} chunks.")

    embedding = get_embedding_model()
    vector_store = get_vector_store(embedding, persist_directory=str(CHROMA_PERSIST_DIR))

    # Normalize source to filename for eval
    for c in chunks:
        c.metadata["source"] = Path(c.metadata.get("source", "unknown")).name

    vector_store.add_documents(chunks)
    # Chroma with persist_directory persists on add
    print(f"Vector store persisted to {CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    run_ingest()
