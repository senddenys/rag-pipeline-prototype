"""
LLM-based response synthesis that cites retrieved context.
Supports: Groq (free API), OpenAI, Ollama (local). First available is used.
"""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.language_models import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import AuthenticationError, RateLimitError

from app.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)


def _format_context(docs: list[Document]) -> str:
    """Format retrieved chunks with source for citations."""
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[{i}] (Source: {source})\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def get_llm() -> BaseLLM | None:
    """Return LLM: Groq (free) > OpenAI > Ollama (local) > None (stub)."""
    if GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model=GROQ_MODEL,
                api_key=GROQ_API_KEY,
                temperature=0,
            )
        except Exception:
            pass
    if OPENAI_API_KEY:
        return ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, temperature=0)
    try:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=0,
        )
    except Exception:
        pass
    return None


SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Answer the user's question using only the provided context. "
               "Cite sources by number, e.g. [1], [2]. If the context does not contain the answer, say so."),
    ("human", "Context:\n\n{context}\n\nQuestion: {question}"),
])


def synthesize(question: str, docs: list[Document], llm: BaseLLM = None) -> str:
    """
    Generate an answer from retrieved docs, with citations.
    If no LLM is configured, returns a stub response listing the context.
    """
    context = _format_context(docs)
    llm = llm or get_llm()

    def _stub_response(reason: str = ""):
        msg = "[Stub response"
        if reason:
            msg += f" — {reason}"
        else:
            msg += " — set a valid OPENAI_API_KEY in .env for real LLM answers"
        msg += ".]\n\nRetrieved context:\n" + context[:1500] + ("..." if len(context) > 1500 else "")
        return msg

    if llm is None:
        return _stub_response()

    try:
        chain = SYNTHESIS_PROMPT | llm
        response = chain.invoke({"context": context, "question": question})
        return response.content if hasattr(response, "content") else str(response)
    except AuthenticationError:
        return _stub_response("invalid or expired API key; check OPENAI_API_KEY in .env")
    except RateLimitError:
        return _stub_response("OpenAI quota exceeded — check plan and billing at platform.openai.com")
    except Exception as e:
        return _stub_response(f"LLM error: {getattr(e, 'message', str(e))[:80]}")
