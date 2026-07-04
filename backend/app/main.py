"""FastAPI surface for the Research Cartographer.

Endpoints:
  GET  /api/health              - ollama + library status
  POST /api/search {topic}      - start a pipeline job, returns {job_id}
  GET  /api/jobs/{id}           - one-shot job status
  GET  /api/jobs/{id}/stream    - SSE stream of job progress (watch stages complete)
  GET  /api/landscapes          - list saved landscapes (the growing reading map)
  GET  /api/landscapes/{id}     - full landscape + papers
  GET  /api/library             - library stats
"""
import asyncio
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import config, store, pipeline, llm

app = FastAPI(title="Research Cartographer", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    store.init()


class SearchReq(BaseModel):
    topic: str = Field(min_length=2, max_length=200)


@app.get("/api/health")
async def health():
    try:
        ol = await llm.health()
    except Exception as e:  # noqa: BLE001
        ol = {"ok": False, "error": str(e)}
    return {"status": "ok", "ollama": ol, "model": config.LLM_MODEL,
            "cross_encoder": config.CROSS_ENCODER_MODEL, "library": store.library_stats()}


@app.post("/api/search")
async def search(req: SearchReq):
    job = pipeline.create_job(req.topic)
    asyncio.create_task(pipeline.run(job))
    return {"job_id": job.id, "topic": job.topic}


@app.get("/api/jobs/{job_id}")
async def job_status(job_id: str):
    job = pipeline.JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job.snapshot()


@app.get("/api/jobs/{job_id}/stream")
async def job_stream(job_id: str):
    job = pipeline.JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")

    async def gen():
        last = -1
        # stream until the job finishes, emitting only on version change
        while True:
            if job.version != last:
                last = job.version
                yield f"data: {json.dumps(job.snapshot())}\n\n"
            if job.status in ("done", "error"):
                break
            await asyncio.sleep(0.4)
        yield f"event: end\ndata: {json.dumps(job.snapshot())}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@app.get("/api/landscapes")
async def landscapes():
    return {"landscapes": store.list_landscapes()}


@app.get("/api/landscapes/{landscape_id}")
async def landscape(landscape_id: str):
    data = store.get_landscape(landscape_id)
    if not data:
        raise HTTPException(404, "landscape not found")
    return data


@app.get("/api/library")
async def library():
    return store.library_stats()
