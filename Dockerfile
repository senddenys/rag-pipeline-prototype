# RAG Pipeline Prototype — optional container run
# Build: docker build -t rag-pipeline .
# Run:   docker run -p 8501:8501 -e GROQ_API_KEY=... rag-pipeline
# Note:  Run ingest once to build chroma_data, or mount a pre-built chroma_data volume.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# .env not copied; use -e GROQ_API_KEY=... or mount .env

EXPOSE 8501

# Default: start Streamlit. To ingest first, override: docker run ... rag-pipeline python -m app.ingest
CMD ["streamlit", "run", "app/chat_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]
