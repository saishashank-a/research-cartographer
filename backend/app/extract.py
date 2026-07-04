"""Stage 3: per-paper structured extraction.

For each top paper the LLM reads title + abstract and returns a compact,
structured card: problem, method, key results, contribution, and 2-4 keywords.
"""
import asyncio

from . import config
from .llm import generate_json, LLMError
from .arxiv_client import Paper

_SYSTEM = (
    "You are a meticulous ML research assistant. You read a paper's title and "
    "abstract and extract a faithful, concise structured summary. Never invent "
    "results that are not stated. Keep each field to 1-2 sentences."
)

_SCHEMA_HINT = (
    '{"problem": str, "method": str, "results": str, "contribution": str, '
    '"keywords": [str, ...]}'
)


def _prompt(paper: Paper) -> str:
    abstract = paper.abstract[: config.MAX_EXTRACT_CHARS]
    return (
        f"Paper title: {paper.title}\n\n"
        f"Abstract: {abstract}\n\n"
        "Extract a structured summary as a JSON object with exactly these keys:\n"
        "  problem       - the research problem / gap it addresses\n"
        "  method        - the core approach or technique\n"
        "  results       - the main quantitative or qualitative findings\n"
        "  contribution  - what is novel / why it matters\n"
        "  keywords      - 2 to 4 short topical tags\n\n"
        f"Return ONLY JSON matching: {_SCHEMA_HINT}"
    )


async def _extract_one(paper: Paper, sem: asyncio.Semaphore) -> Paper:
    async with sem:
        try:
            data = await generate_json(_prompt(paper), system=_SYSTEM)
        except LLMError:
            data = {}
        paper.extraction = {
            "problem": str(data.get("problem", "")).strip(),
            "method": str(data.get("method", "")).strip(),
            "results": str(data.get("results", "")).strip(),
            "contribution": str(data.get("contribution", "")).strip(),
            "keywords": [str(k).strip() for k in (data.get("keywords") or [])][:4],
        }
        return paper


async def extract_all(papers: list[Paper], concurrency: int = 3,
                      on_progress=None) -> list[Paper]:
    """Extract structured cards for all papers with bounded concurrency.

    on_progress(done, total) is called after each paper completes so the UI
    can show incremental progress within the extraction stage.
    """
    sem = asyncio.Semaphore(concurrency)
    total = len(papers)
    done = 0
    results: list[Paper] = []
    tasks = [asyncio.create_task(_extract_one(p, sem)) for p in papers]
    for coro in asyncio.as_completed(tasks):
        results.append(await coro)
        done += 1
        if on_progress:
            on_progress(done, total)
    # preserve original (rerank) ordering
    order = {p.arxiv_id: i for i, p in enumerate(papers)}
    results.sort(key=lambda p: order.get(p.arxiv_id, 0))
    return results
