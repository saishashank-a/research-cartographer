"""Stage 4: cross-paper synthesis into a research landscape.

Takes the structured cards for all top papers and asks the LLM to reason
ACROSS them: group into thematic clusters, name relationships between clusters,
surface tensions/disagreements, and list open problems. This is where a flat
list of papers becomes a map of a field.
"""
from . import config
from .llm import generate_json, LLMError
from .arxiv_client import Paper

_SYSTEM = (
    "You are a senior ML researcher writing a survey. You reason across many "
    "papers to reveal the structure of a research field: its sub-areas, how they "
    "relate, where they disagree, and what remains unsolved. Be specific and cite "
    "papers by their index number in square brackets, e.g. [2]."
)


def _papers_block(papers: list[Paper]) -> str:
    lines = []
    for i, p in enumerate(papers):
        ex = p.extraction or {}
        lines.append(
            f"[{i}] {p.title} ({p.published})\n"
            f"    problem: {ex.get('problem','')}\n"
            f"    method: {ex.get('method','')}\n"
            f"    results: {ex.get('results','')}\n"
            f"    contribution: {ex.get('contribution','')}\n"
            f"    keywords: {', '.join(ex.get('keywords', []))}"
        )
    return "\n".join(lines)


_SCHEMA_HINT = """{
  "summary": "2-3 sentence overview of the field as represented by these papers",
  "clusters": [
    {"name": "short cluster name",
     "description": "1-2 sentences on what unites these papers",
     "paper_indices": [int, ...]}
  ],
  "relationships": [
    {"from": "cluster name", "to": "cluster name", "relation": "builds-on | competes-with | complements | enables"}
  ],
  "tensions": ["a specific disagreement or trade-off across the papers", ...],
  "open_problems": ["a concrete unsolved problem the field is circling", ...]
}"""


def _prompt(topic: str, papers: list[Paper]) -> str:
    return (
        f"Research topic searched: \"{topic}\"\n\n"
        f"Here are {len(papers)} of the most relevant papers, each with a "
        f"structured card:\n\n{_papers_block(papers)}\n\n"
        "Synthesize these into a research landscape. Group the papers into 3-6 "
        "thematic clusters (every paper index must appear in exactly one cluster), "
        "describe the relationships BETWEEN clusters, surface 2-4 genuine tensions "
        "or trade-offs, and list 3-6 concrete open problems.\n\n"
        f"Return ONLY a JSON object matching this shape:\n{_SCHEMA_HINT}"
    )


def _coerce(landscape: dict, papers: list[Paper]) -> dict:
    """Normalise the model output and guarantee every paper is placed."""
    n = len(papers)
    clusters = []
    seen = set()
    for c in (landscape.get("clusters") or []):
        idxs = [i for i in (c.get("paper_indices") or []) if isinstance(i, int) and 0 <= i < n]
        idxs = [i for i in idxs if i not in seen]
        seen.update(idxs)
        clusters.append({
            "name": str(c.get("name", "Cluster")).strip() or "Cluster",
            "description": str(c.get("description", "")).strip(),
            "paper_indices": idxs,
        })
    # any unplaced papers -> "Other"
    leftover = [i for i in range(n) if i not in seen]
    if leftover:
        clusters.append({"name": "Other", "description": "Papers not grouped above.",
                         "paper_indices": leftover})
    clusters = [c for c in clusters if c["paper_indices"]]
    return {
        "summary": str(landscape.get("summary", "")).strip(),
        "clusters": clusters,
        "relationships": [
            {"from": str(r.get("from", "")).strip(),
             "to": str(r.get("to", "")).strip(),
             "relation": str(r.get("relation", "relates-to")).strip()}
            for r in (landscape.get("relationships") or [])
            if r.get("from") and r.get("to")
        ],
        "tensions": [str(t).strip() for t in (landscape.get("tensions") or []) if str(t).strip()],
        "open_problems": [str(o).strip() for o in (landscape.get("open_problems") or []) if str(o).strip()],
    }


async def synthesize(topic: str, papers: list[Paper]) -> dict:
    if not papers:
        return {"summary": "", "clusters": [], "relationships": [],
                "tensions": [], "open_problems": []}
    try:
        landscape = await generate_json(_prompt(topic, papers), system=_SYSTEM,
                                        temperature=0.3)
    except LLMError:
        # graceful fallback: one cluster, no cross-paper structure
        landscape = {"summary": "", "clusters": [
            {"name": "All papers", "description": "", "paper_indices": list(range(len(papers)))}
        ]}
    return _coerce(landscape, papers)
