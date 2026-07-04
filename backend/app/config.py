"""Central configuration. All values overridable via environment variables."""
import os

# --- Ollama (local LLM) -----------------------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
# Model used for structured extraction + landscape synthesis (reasoning).
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
# Optional cheaper/faster model for lightweight relevance pre-scoring.
LLM_FAST_MODEL = os.getenv("LLM_FAST_MODEL", LLM_MODEL)
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "180"))

# --- Cross-encoder reranker -------------------------------------------------
CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

# --- Retrieval / pipeline sizing --------------------------------------------
ARXIV_CANDIDATES = int(os.getenv("ARXIV_CANDIDATES", "40"))   # papers pulled from arXiv
TOP_K = int(os.getenv("TOP_K", "12"))                         # papers kept after rerank
MAX_EXTRACT_CHARS = int(os.getenv("MAX_EXTRACT_CHARS", "6000"))

# --- Storage ----------------------------------------------------------------
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "cartographer.db"))
DB_PATH = os.path.abspath(DB_PATH)

# --- Server -----------------------------------------------------------------
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
