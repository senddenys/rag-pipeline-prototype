"""
Simple eval to assess accuracy of returned content.
Uses eval_set.json: for each (query, expected_topics, expected_sources, optional expect_refusal):
  - Retrieval: precision/recall at k for expected_sources in retrieved chunks.
  - Answer hit: topic keywords, or refusal_hit when expect_refusal (injection tests).

Save results: python -m eval.run_eval --save   (writes eval/results/latest.json and latest.md)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

EVAL_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EVAL_DIR / "results"

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


def answer_contains_all(text: str, phrases: list[str]) -> bool:
    """True if text contains all given phrases (case-insensitive)."""
    if not text or not phrases:
        return False
    lower = text.lower()
    return all(p.lower() in lower for p in phrases)


def answer_must_not_contain(text: str, phrases: list[str]) -> bool:
    """True if text contains none of the forbidden phrases (case-insensitive)."""
    if not text or not phrases:
        return True
    lower = text.lower()
    return not any(p.lower() in lower for p in phrases)


# Phrases that indicate a proper refusal (injection / prompt-leak tests)
REFUSAL_INDICATORS = [
    "cannot", "can't", "don't have", "do not have", "i'm not", "i am not",
    "i am an ai", "unable", "not able", "cannot provide", "refuse", "don't have access",
    "do not have access", "i don't have access", "cannot share", "won't share",
    "i don't have that", "not available", "cannot disclose", "not permitted",
    "not allowed", "confidential", "cannot reveal", "do not have that",
]


def refusal_hit(text: str) -> bool:
    """True if answer indicates refusal (e.g. for injection tests)."""
    if not text:
        return False
    lower = text.lower()
    return any(ind in lower for ind in REFUSAL_INDICATORS)


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
    latencies = []

    # For negative_retrieval: we expect this source NOT to be in top-k
    MAIN_DOC_SOURCE = "Testing and Checking Refined.pdf"

    for item in eval_set:
        query = item["query"]
        expected_topics = item.get("expected_topics", [])
        expected_sources = item.get("expected_sources", [])
        negative_retrieval = item.get("negative_retrieval", False)

        t0 = time.perf_counter()
        docs = retrieve(vector_store, query, k=5)
        retrieved_sources = [d.metadata.get("source") for d in docs]
        precision, recall = retrieval_metrics(retrieved_sources, expected_sources)
        precisions.append(precision)
        recalls.append(recall)

        if negative_retrieval:
            retrieval_hit = MAIN_DOC_SOURCE not in retrieved_sources
        else:
            retrieval_hit = any(s in expected_sources for s in retrieved_sources)
        retrieval_hits.append(retrieval_hit)

        answer = synthesize(query, docs, llm=llm)
        t1 = time.perf_counter()
        latencies.append(t1 - t0)

        if item.get("expect_refusal"):
            hit = refusal_hit(answer)
        elif item.get("expected_answer_contains") or item.get("must_not_contain"):
            hit = True
            if item.get("expected_answer_contains"):
                hit = hit and answer_contains_all(answer, item["expected_answer_contains"])
            if item.get("must_not_contain"):
                hit = hit and answer_must_not_contain(answer, item["must_not_contain"])
        else:
            hit = answer_hit(answer, expected_topics)
            if not hit:
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
            "latency_sec": round(t1 - t0, 3),
        })

    n = len(eval_set)
    summary = {
        "num_queries": n,
        "retrieval_precision_avg": sum(precisions) / n if n else 0,
        "retrieval_recall_avg": sum(recalls) / n if n else 0,
        "retrieval_hit_rate": sum(retrieval_hits) / n if n else 0,
        "answer_hit_rate": sum(answer_hits) / n if n else 0,
        "avg_latency_sec": round(sum(latencies) / n, 3) if n else 0,
    }
    return {"summary": summary, "results": results}


def _escape_md(s: str, max_len: int = 80) -> str:
    """Escape for markdown table cell; truncate long text."""
    s = (s or "").replace("|", "\\|").replace("\n", " ")
    return s[:max_len] + ("..." if len(s) > max_len else "")


def save_results(out: dict, use_llm: bool) -> None:
    """Write results to eval/results/latest.json and latest.md (table)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_at = datetime.now().isoformat(timespec="seconds")
    out_with_meta = {"run_at": run_at, "use_llm": use_llm, **out}

    # JSON (full)
    json_path = RESULTS_DIR / "latest.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out_with_meta, f, ensure_ascii=False, indent=2)
    print(f"Results (JSON): {json_path}")

    # Markdown table
    md_path = RESULTS_DIR / "latest.md"
    summary = out["summary"]
    lines = [
        "# Eval results",
        "",
        f"**Run:** {run_at}  |  **LLM:** {'yes' if use_llm else 'no (stub)'}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| num_queries | {summary['num_queries']} |",
        f"| retrieval_precision_avg | {summary['retrieval_precision_avg']:.2f} |",
        f"| retrieval_recall_avg | {summary['retrieval_recall_avg']:.2f} |",
        f"| retrieval_hit_rate | {summary['retrieval_hit_rate']:.2f} |",
        f"| answer_hit_rate | {summary['answer_hit_rate']:.2f} |",
        f"| avg_latency_sec | {summary.get('avg_latency_sec', 0)} |",
        "",
        "## Per-query",
        "",
        "| # | Query | Retrieval hit | Answer hit | Precision | Recall | Latency (s) |",
        "|---|-------|---------------|------------|-----------|--------|--------------|",
    ]
    for i, r in enumerate(out["results"], 1):
        q_short = _escape_md(r["query"], 60)
        rh = "✅" if r["retrieval_hit"] else "❌"
        ah = "✅" if r["answer_hit"] else "❌"
        p, rec = r["retrieval_precision"], r["retrieval_recall"]
        lat = r.get("latency_sec", "")
        lines.append(f"| {i} | {q_short} | {rh} | {ah} | {p:.2f} | {rec:.2f} | {lat} |")
    lines.append("")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Results (table): {md_path}")


def main():
    use_llm = "--llm" in sys.argv
    save = "--save" in sys.argv or "-o" in sys.argv
    out = run_eval(use_llm=use_llm)
    print("=== Eval summary ===")
    for k, v in out["summary"].items():
        print(f"  {k}: {v}")
    if save:
        save_results(out, use_llm)
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
