"""SQLite persistence: the reading map that grows over time.

Every completed search is saved as a landscape row plus its papers. Papers are
de-duplicated by arxiv_id across searches so the global reading map accumulates
a growing, cross-topic library instead of starting fresh each time.
"""
import json
import sqlite3
import time
from contextlib import contextmanager

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS landscapes (
    id          TEXT PRIMARY KEY,
    topic       TEXT NOT NULL,
    created_at  REAL NOT NULL,
    summary     TEXT,
    data        TEXT NOT NULL      -- full landscape JSON (clusters, relationships, ...)
);
CREATE TABLE IF NOT EXISTS papers (
    arxiv_id     TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    abstract     TEXT,
    authors      TEXT,             -- JSON array
    published    TEXT,
    categories   TEXT,             -- JSON array
    pdf_url      TEXT,
    abs_url      TEXT,
    extraction   TEXT,             -- JSON object
    first_seen   REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS landscape_papers (
    landscape_id  TEXT NOT NULL,
    arxiv_id      TEXT NOT NULL,
    rerank_score  REAL,
    PRIMARY KEY (landscape_id, arxiv_id)
);
"""


@contextmanager
def _conn():
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init():
    with _conn() as con:
        con.executescript(_SCHEMA)


def save_landscape(landscape_id: str, topic: str, papers: list, landscape: dict):
    now = time.time()
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO landscapes (id, topic, created_at, summary, data) "
            "VALUES (?,?,?,?,?)",
            (landscape_id, topic, now, landscape.get("summary", ""), json.dumps(landscape)),
        )
        for p in papers:
            con.execute(
                "INSERT INTO papers (arxiv_id,title,abstract,authors,published,categories,"
                "pdf_url,abs_url,extraction,first_seen) VALUES (?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(arxiv_id) DO UPDATE SET extraction=excluded.extraction",
                (p.arxiv_id, p.title, p.abstract, json.dumps(p.authors), p.published,
                 json.dumps(p.categories), p.pdf_url, p.abs_url,
                 json.dumps(p.extraction), now),
            )
            con.execute(
                "INSERT OR REPLACE INTO landscape_papers (landscape_id,arxiv_id,rerank_score) "
                "VALUES (?,?,?)",
                (landscape_id, p.arxiv_id, p.rerank_score),
            )


def _paper_row(row, score=None) -> dict:
    return {
        "arxiv_id": row["arxiv_id"],
        "title": row["title"],
        "abstract": row["abstract"],
        "authors": json.loads(row["authors"] or "[]"),
        "published": row["published"],
        "categories": json.loads(row["categories"] or "[]"),
        "pdf_url": row["pdf_url"],
        "abs_url": row["abs_url"],
        "extraction": json.loads(row["extraction"] or "{}"),
        "rerank_score": score,
    }


def get_landscape(landscape_id: str) -> dict | None:
    with _conn() as con:
        ls = con.execute("SELECT * FROM landscapes WHERE id=?", (landscape_id,)).fetchone()
        if not ls:
            return None
        rows = con.execute(
            "SELECT p.*, lp.rerank_score AS score FROM landscape_papers lp "
            "JOIN papers p ON p.arxiv_id = lp.arxiv_id WHERE lp.landscape_id=? "
            "ORDER BY lp.rerank_score DESC",
            (landscape_id,),
        ).fetchall()
        papers = [_paper_row(r, r["score"]) for r in rows]
        return {
            "id": ls["id"], "topic": ls["topic"], "created_at": ls["created_at"],
            "landscape": json.loads(ls["data"]), "papers": papers,
        }


def list_landscapes() -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT l.id,l.topic,l.created_at,l.summary,"
            "(SELECT COUNT(*) FROM landscape_papers lp WHERE lp.landscape_id=l.id) AS n "
            "FROM landscapes l ORDER BY l.created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def library_stats() -> dict:
    with _conn() as con:
        n_papers = con.execute("SELECT COUNT(*) c FROM papers").fetchone()["c"]
        n_ls = con.execute("SELECT COUNT(*) c FROM landscapes").fetchone()["c"]
        return {"total_papers": n_papers, "total_landscapes": n_ls}
