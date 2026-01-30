# RAG Pipeline Prototype

Minimal Retrieval-Augmented Generation (RAG) application with **evaluation** focus: ingestion, chunking, embeddings, vector search (ChromaDB), and LLM synthesis with citations. Includes unit tests, E2E tests, and a simple eval setup to assess accuracy of returned content.

## Features

- **Ingestion & chunking** — Load Markdown/PDF, split into chunks
- **Embeddings** — Local sentence-transformers (or configurable)
- **Vector store** — ChromaDB (local, no API key)
- **Retrieval + synthesis** — Similarity search → LLM with cited context
- **Chat UI** — Simple Streamlit: one input, response area
- **Eval** — Unit/E2E tests + script to measure retrieval/answer accuracy

## Requirements

- Python 3.10+
- **Free LLM:** Groq API key (no card) or Ollama (local). Optional: OpenAI.

## Setup

```bash
cd rag-pipeline-prototype
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# For free real answers: get a key at https://console.groq.com and set GROQ_API_KEY in .env
```

## Free LLM: Groq (recommended)

1. Go to **https://console.groq.com** and sign up (email or GitHub).
2. Create an API key in the console.
3. In `.env` set: `GROQ_API_KEY=gsk_your_key_here`
4. Restart Streamlit. Answers will use Groq (free tier, no credit card).

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | **Free.** If set, used first for LLM (get key at console.groq.com). |
| `OPENAI_API_KEY` | Optional. Used if GROQ not set; requires billing. |
| `OLLAMA_BASE_URL` | Optional. If Ollama runs locally, e.g. `http://localhost:11434` |
| `CHROMA_PERSIST_DIR` | Optional. Default: `./chroma_data` |

## Run Locally

1. **Ingest content** (build vector store from `content/`):

   ```bash
   python -m app.ingest
   ```

2. **Start the chat UI**:

   ```bash
   streamlit run app/chat_ui.py
   ```

   Open the URL shown (e.g. http://localhost:8501). Type a question and get a response with cited chunks.

## Running Tests

- **Unit + E2E tests:**

  ```bash
  pytest tests/ -v
  ```

- **Evaluation (accuracy of retrieval/answers):**

  ```bash
  python -m eval.run_eval
  ```

  Uses `eval/eval_set.json` (query + expected topics/sources) and prints retrieval and answer-level metrics. See [Eval](#evaluation) below.

## Project Layout

```
rag-pipeline-prototype/
├── app/
│   ├── ingest.py       # Load & chunk content, build ChromaDB
│   ├── retrieval.py    # Embeddings, vector store, retrieval
│   ├── synthesis.py    # LLM synthesis with citations
│   └── chat_ui.py      # Streamlit UI
├── content/            # Source documents (MD/PDF)
├── eval/
│   ├── eval_set.json   # (query, expected) pairs
│   └── run_eval.py     # Eval script
├── tests/
│   ├── test_ingest.py
│   ├── test_retrieval.py
│   └── test_e2e.py
├── requirements.txt
├── .env.example
└── README.md
```

## Evaluation

The eval setup is kept **simple** to assess accuracy of returned content:

1. **Eval set** (`eval/eval_set.json`): list of `{ "query": "...", "expected_topics": ["..."], "expected_sources": ["..."] }`. Expected topics/sources are used to compute:
   - **Retrieval**: whether the right chunks (by source/topic) appear in top-k.
   - **Answer relevance**: whether the model’s answer (or cited chunks) contain the expected topics/sources.

2. **Metrics** (printed by `run_eval.py`):
   - **Retrieval precision/recall** (at k=5): overlap of retrieved chunk sources with `expected_sources`.
   - **Answer hit**: for each query, whether the final answer (or citations) mention expected topics/sources (keyword overlap).

3. **How to run:** `python -m eval.run_eval` (after `python -m app.ingest` so the vector store exists).

You can extend `eval_set.json` with more queries and expected values to better reflect your content.

## Design Notes

- **Chunking**: Recursive character splitter; chunk size and overlap can be tuned in `app/ingest.py`.
- **Embeddings**: Local by default (sentence-transformers) so the pipeline runs without extra API keys for indexing.
- **LLM**: Groq (free, no card) first; then OpenAI or local Ollama. Without any key, the app shows a stub response so UI and retrieval still work.
- **Containers**: Back-end can be containerized later (e.g. Dockerfile for `app/ingest` + `streamlit run`); not required for this prototype.

## License

MIT (or as required by your organization).
