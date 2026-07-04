"""The four-stage pipeline + an in-memory job registry that streams progress.

Stages:
  1. retrieve   - arXiv pulls candidate papers
  2. rerank     - cross-encoder reranks by semantic relevance, keep top-K
  3. extract    - per-paper structured extraction (problem/method/results/...)
  4. synthesize - cross-paper synthesis into a research landscape

A Job holds the live status of each stage so the UI can watch each one complete.
"""
import asyncio
import time
import uuid
from dataclasses import dataclass, field

from . import arxiv_client, rerank, extract, synthesize, store, config

STAGES = ["retrieve", "rerank", "extract", "synthesize"]


@dataclass
class Stage:
    name: str
    status: str = "pending"      # pending | running | done | error
    detail: str = ""
    progress: float = 0.0        # 0..1 within the stage


@dataclass
class Job:
    id: str
    topic: str
    created_at: float = field(default_factory=time.time)
    status: str = "running"      # running | done | error
    stages: dict = field(default_factory=lambda: {s: Stage(s) for s in STAGES})
    landscape_id: str | None = None
    error: str | None = None
    version: int = 0             # bumped on every mutation for SSE change-detection

    def touch(self, **_):
        self.version += 1

    def snapshot(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "status": self.status,
            "landscape_id": self.landscape_id,
            "error": self.error,
            "version": self.version,
            "stages": [
                {"name": s.name, "status": s.status, "detail": s.detail,
                 "progress": round(s.progress, 3)}
                for s in self.stages.values()
            ],
        }


JOBS: dict[str, Job] = {}


def create_job(topic: str) -> Job:
    job = Job(id=uuid.uuid4().hex[:12], topic=topic.strip())
    JOBS[job.id] = job
    return job


def _set(job: Job, stage: str, *, status=None, detail=None, progress=None):
    st = job.stages[stage]
    if status is not None:
        st.status = status
    if detail is not None:
        st.detail = detail
    if progress is not None:
        st.progress = progress
    job.touch()


async def run(job: Job):
    try:
        # ---- Stage 1: retrieve --------------------------------------------
        _set(job, "retrieve", status="running", detail="Querying arXiv…")
        papers = await arxiv_client.search(job.topic, config.ARXIV_CANDIDATES)
        if not papers:
            raise RuntimeError("arXiv returned no papers for this topic.")
        _set(job, "retrieve", status="done",
             detail=f"Pulled {len(papers)} candidate papers", progress=1.0)

        # ---- Stage 2: rerank ----------------------------------------------
        _set(job, "rerank", status="running",
             detail="Scoring relevance with cross-encoder…")
        top = await rerank.rerank(job.topic, papers, config.TOP_K)
        _set(job, "rerank", status="done",
             detail=f"Kept top {len(top)} by semantic relevance", progress=1.0)

        # ---- Stage 3: extract ---------------------------------------------
        _set(job, "extract", status="running", detail="Reading papers…")

        def on_prog(done, total):
            _set(job, "extract", detail=f"Read {done}/{total} papers",
                 progress=done / total)

        top = await extract.extract_all(top, concurrency=3, on_progress=on_prog)
        _set(job, "extract", status="done",
             detail=f"Extracted {len(top)} structured cards", progress=1.0)

        # ---- Stage 4: synthesize ------------------------------------------
        _set(job, "synthesize", status="running",
             detail="Synthesizing the research landscape…")
        landscape = await synthesize.synthesize(job.topic, top)
        _set(job, "synthesize", status="done",
             detail=f"{len(landscape['clusters'])} clusters, "
                    f"{len(landscape['open_problems'])} open problems", progress=1.0)

        # ---- persist -------------------------------------------------------
        landscape_id = job.id
        store.save_landscape(landscape_id, job.topic, top, landscape)
        job.landscape_id = landscape_id
        job.status = "done"
        job.touch()
    except Exception as e:  # noqa: BLE001 - surface any failure to the UI
        job.status = "error"
        job.error = str(e)
        # mark whichever stage was running as errored
        for st in job.stages.values():
            if st.status == "running":
                st.status = "error"
                st.detail = str(e)
        job.touch()
