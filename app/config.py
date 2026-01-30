"""App configuration from environment."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = PROJECT_ROOT / "content"
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "chroma_data")))
EVAL_SET_PATH = PROJECT_ROOT / "eval" / "eval_set.json"

# Embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# LLM (first set wins: Groq → OpenAI → Ollama)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Free: console.groq.com
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")  # Local: ollama run llama3.2
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Chunking
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# Retrieval
TOP_K = int(os.getenv("TOP_K", "5"))
