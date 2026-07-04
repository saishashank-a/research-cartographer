"""arXiv retrieval. arXiv handles retrieval; the LLM does the reading."""
import asyncio
from dataclasses import dataclass, field, asdict

import arxiv

from . import config


@dataclass
class Paper:
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str]
    published: str
    updated: str
    categories: list[str]
    pdf_url: str
    abs_url: str
    # filled in by later pipeline stages
    rerank_score: float = 0.0
    extraction: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def _search_sync(query: str, limit: int) -> list[Paper]:
    client = arxiv.Client(page_size=min(limit, 100), delay_seconds=3, num_retries=3)
    search = arxiv.Search(
        query=query,
        max_results=limit,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    papers: list[Paper] = []
    for r in client.results(search):
        papers.append(Paper(
            arxiv_id=r.get_short_id(),
            title=r.title.strip().replace("\n", " "),
            abstract=r.summary.strip().replace("\n", " "),
            authors=[a.name for a in r.authors][:12],
            published=r.published.date().isoformat() if r.published else "",
            updated=r.updated.date().isoformat() if r.updated else "",
            categories=list(r.categories),
            pdf_url=r.pdf_url,
            abs_url=r.entry_id,
        ))
    return papers


async def search(query: str, limit: int | None = None) -> list[Paper]:
    """Async wrapper — the arxiv library is blocking, so run it off-thread."""
    limit = limit or config.ARXIV_CANDIDATES
    return await asyncio.to_thread(_search_sync, query, limit)
