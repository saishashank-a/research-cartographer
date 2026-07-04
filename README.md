# 🗺️ Research Cartographer

Map an entire ML research field from a single search — **100% local, no API keys.**

Enter a topic in plain English → arXiv pulls candidate papers → a cross-encoder reranks by
semantic relevance → a local LLM reads each paper and extracts structured cards → the model
synthesizes across all of them into a **research landscape** (clusters, relationships, tensions,
open problems). Every search is saved into a reading map that grows over time.

## Pipeline

| Stage | What happens | Powered by |
|-------|--------------|-----------|
| 1. Retrieve | Pull ~40 candidate papers | arXiv |
| 2. Rerank | Score (query, paper) pairs, keep top 12 | cross-encoder (ms-marco-MiniLM) |
| 3. Extract | Read each paper → problem / method / results / contribution | local LLM (Ollama) |
| 4. Synthesize | Reason across papers → clusters, relationships, tensions, open problems | local LLM (Ollama) |

## Stack
- **Backend:** FastAPI + arXiv + sentence-transformers cross-encoder + Ollama, SQLite persistence, SSE progress stream
- **Frontend:** Next.js 15 + Tailwind, live pipeline view, interactive landscape
- **LLM:** fully local via [Ollama](https://ollama.com) — no cloud, no API keys, no per-query cost

## Prerequisites
- [Ollama](https://ollama.com) running with a chat model: `ollama pull qwen2.5:7b`
- Python 3.10+ and Node 18+

## Run

**1. Backend**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# make sure ollama is running:  ollama serve
uvicorn app.main:app --reload --port 8000
```

**2. Frontend** (new terminal)
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 and search any ML topic.

## Configuration
All via environment variables (see `backend/app/config.py`):
- `LLM_MODEL` (default `qwen2.5:7b`) — the model used for extraction + synthesis
- `OLLAMA_HOST` (default `http://localhost:11434`)
- `ARXIV_CANDIDATES` (default 40) / `TOP_K` (default 12)
- `CROSS_ENCODER_MODEL` (default `cross-encoder/ms-marco-MiniLM-L-6-v2`)

## Notes
- First backend run downloads the cross-encoder model (~90 MB) once.
- Extraction runs 3 papers concurrently; a full map takes ~1–3 min on a 7B local model.
- Data persists in `backend/cartographer.db` (SQLite) — the reading map survives restarts.
