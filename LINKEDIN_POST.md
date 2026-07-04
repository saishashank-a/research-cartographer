# LinkedIn Post — Research Cartographer

> Attach the screenshots in this order: 01_landscape_hero → 02_pipeline_running → 04_tensions_openproblems → 03_landscape_moe (from the `screenshots/` folder).

---

## Option A — the "builder" version (recommended)

I built an AI agent that maps an entire ML research field from a single search — and it runs 100% on my laptop. No API keys. No per-token bill.

Type a topic in plain English ("retrieval augmented generation", "mixture of experts") and a four-stage pipeline runs while you watch each step finish:

🔍 Retrieve — arXiv pulls ~40 candidate papers
⇅ Rerank — a cross-encoder scores every paper against your query for true semantic relevance, keeps the top 12
❏ Extract — a local LLM reads each paper and pulls out a structured card: problem, method, results, contribution
✦ Synthesize — the model reasons ACROSS all the papers to build a research landscape: thematic clusters, how they relate, the field's open tensions, and the unsolved problems

The output isn't a list of links — it's a map. For RAG it surfaced clusters like "privacy & security" and "evaluation & robustness," flagged the real tension between retrieval efficiency and answer coherence, and listed open problems like unified RAG evaluation and defenses against corpus poisoning. Every search is saved, so the reading map grows into your own living library.

The part I'm proudest of: it's fully local. arXiv handles retrieval; Ollama (running qwen2.5 on my machine) does all the reading, ranking, and synthesis. Nothing leaves the laptop, nothing costs a cent per query.

Stack:
• FastAPI + arXiv + a cross-encoder reranker (backend)
• Local LLM via Ollama — no cloud, no keys
• Next.js + Tailwind (frontend) with a live SSE progress stream

Turns out you don't need a frontier API to build a genuinely useful research agent. A 7B model, a good reranker, and the right pipeline design go a long way.

More agent projects coming. 👇 What field should I map next?

#MachineLearning #LLM #AIAgents #LocalLLM #Ollama #RAG #OpenSource #BuildInPublic

---

## Option B — shorter / punchier

Most "AI research assistants" just give you a longer list of links.

I wanted a map. So I built one — and it runs entirely on my laptop, no API keys, no cost.

Search any ML topic → arXiv pulls the papers → a cross-encoder reranks by relevance → a local LLM reads each one → then it synthesizes across all of them into clusters, relationships, tensions, and open problems. You watch all four stages run live.

For "retrieval augmented generation" it drew out privacy vs. evaluation clusters, the efficiency-vs-coherence tension, and named the field's open problems — in about two minutes, on-device.

Stack: FastAPI + arXiv + cross-encoder + Ollama (local qwen2.5) + Next.js/Tailwind.

The lesson: a 7B model + a solid reranker + good pipeline design beats "just call a big API" for a lot of real agent work.

What field should I point it at next?

#AIAgents #LocalLLM #MachineLearning #Ollama #BuildInPublic
