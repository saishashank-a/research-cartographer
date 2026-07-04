"""Stage 2 (part): cross-encoder semantic reranking.

A cross-encoder scores (query, paper) pairs jointly, which is far more faithful
to true semantic relevance than embedding cosine similarity. The model is loaded
lazily and cached, and scoring runs off the event loop.
"""
import asyncio
import math

from . import config
from .arxiv_client import Paper

_model = None


def _get_model():
    global _model
    if _model is None:
        # imported lazily so the server can boot before torch is warm
        from sentence_transformers import CrossEncoder
        _model = CrossEncoder(config.CROSS_ENCODER_MODEL)
    return _model


def _score_sync(query: str, papers: list[Paper]) -> list[Paper]:
    model = _get_model()
    pairs = [(query, f"{p.title}. {p.abstract}") for p in papers]
    scores = model.predict(pairs, show_progress_bar=False)
    for p, s in zip(papers, scores):
        # ms-marco cross-encoders output a logit; squash to 0..1 for display
        p.rerank_score = round(1.0 / (1.0 + math.exp(-float(s))), 4)
    papers.sort(key=lambda p: p.rerank_score, reverse=True)
    return papers


async def rerank(query: str, papers: list[Paper], top_k: int | None = None) -> list[Paper]:
    top_k = top_k or config.TOP_K
    if not papers:
        return []
    ranked = await asyncio.to_thread(_score_sync, query, papers)
    return ranked[:top_k]
