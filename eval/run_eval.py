"""
Simple eval to assess accuracy of returned content.
Uses eval_set.json: for each (query, expected_topics, expected_sources):
  - Retrieval: precision/recall at k for expected_sources in retrieved chunks.
  - Answer hit: whether the answer (or retrieved chunk text) contains expected topics.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import CHROMA_PERSIST_DIR, EVAL_SET_PATH
from app.retrieval import get_embedding_model, get_vector_store, retrieve
from app.synthesis import synthesize


def load_eval_set(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def retrieval_metrics(retrieved_sources: list[str], expected_sources: list[str]) -> tuple[float, float]:
    """Precision and recall: expected_sources vs retrieved_sources (at k)."""
    retrieved_set = set(s for s in retrieved_sources if s)
    expected_set = set(expected_sources)
    if not expected_set:
        return 0.0, 0.0
    tp = len(retrieved_set & expected_set)
    precision = tp / len(retrieved_set) if retrieved_set else 0.0
    recall = tp / len(expected_set)
    return precision, recall


def answer_hit(text: str, expected_topics: list[str]) -> bool:
    """True if text (answer or chunk) contains at least one expected topic (case-insensitive)."""
    if not text or not expected_topics:
        return False
    lower = text.lower()
    return any(t.lower() in lower for t in expected_topics)


def run_eval(use_llm: bool = False) -> dict:
    if not EVAL_SET_PATH.exists():
        raise FileNotFoundError(f"Eval set not found: {EVAL_SET_PATH}")
    if not CHROMA_PERSIST_DIR.exists():
        raise FileNotFoundError(
            f"Chroma not found at {CHROMA_PERSIST_DIR}. Run: python -m app.ingest"
        )

    eval_set = load_eval_set(EVAL_SET_PATH)
    embedding = get_embedding_model()
    vector_store = get_vector_store(embedding, persist_directory=str(CHROMA_PERSIST_DIR))
    llm = None
    if use_llm:
        from app.synthesis import get_llm
        llm = get_llm()

    results = []
    precisions = []
    recalls = []
    retrieval_hits = []
    answer_hits = []

    for item in eval_set:
        query = item["query"]
        expected_topics = item.get("expected_topics", [])
        expected_sources = item.get("expected_sources", [])

        docs = retrieve(vector_store, query, k=5)
        retrieved_sources = [d.metadata.get("source") for d in docs]
        precision, recall = retrieval_metrics(retrieved_sources, expected_sources)
        precisions.append(precision)
        recalls.append(recall)
        retrieval_hit = any(s in expected_sources for s in retrieved_sources)
        retrieval_hits.append(retrieval_hit)

        answer = synthesize(query, docs, llm=llm)
        hit = answer_hit(answer, expected_topics)
        if not hit:
            # Fallback: any retrieved chunk contains expected topic
            for d in docs:
                if answer_hit(d.page_content, expected_topics):
                    hit = True
                    break
        answer_hits.append(hit)

        results.append({
            "query": query,
            "answer": answer,
            "retrieval_precision": precision,
            "retrieval_recall": recall,
            "retrieval_hit": retrieval_hit,
            "answer_hit": hit,
        })

    n = len(eval_set)
    summary = {
        "num_queries": n,
        "retrieval_precision_avg": sum(precisions) / n if n else 0,
        "retrieval_recall_avg": sum(recalls) / n if n else 0,
        "retrieval_hit_rate": sum(retrieval_hits) / n if n else 0,
        "answer_hit_rate": sum(answer_hits) / n if n else 0,
    }
    return {"summary": summary, "results": results}


def main():
    use_llm = "--llm" in sys.argv
    out = run_eval(use_llm=use_llm)
    print("=== Eval summary ===")
    for k, v in out["summary"].items():
        print(f"  {k}: {v}")
    print("\n=== Per-query (question + answer) ===")
    for i, r in enumerate(out["results"], 1):
        q = r["query"]
        a = r.get("answer", "")
        print(f"\n--- [{i}] Q: {q}")
        print(f"     A: {a[:800]}{'...' if len(a) > 800 else ''}")
        print(f"     retrieval P/R: {r['retrieval_precision']:.2f} / {r['retrieval_recall']:.2f}  hit={r['retrieval_hit']}  answer_hit={r['answer_hit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
