// API client + shared types for the Research Cartographer backend.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export type StageStatus = "pending" | "running" | "done" | "error";

export interface Stage {
  name: string;
  status: StageStatus;
  detail: string;
  progress: number;
}

export interface JobSnapshot {
  id: string;
  topic: string;
  status: "running" | "done" | "error";
  landscape_id: string | null;
  error: string | null;
  version: number;
  stages: Stage[];
}

export interface Extraction {
  problem: string;
  method: string;
  results: string;
  contribution: string;
  keywords: string[];
}

export interface Paper {
  arxiv_id: string;
  title: string;
  abstract: string;
  authors: string[];
  published: string;
  categories: string[];
  pdf_url: string;
  abs_url: string;
  extraction: Extraction;
  rerank_score: number | null;
}

export interface Cluster {
  name: string;
  description: string;
  paper_indices: number[];
}

export interface Relationship {
  from: string;
  to: string;
  relation: string;
}

export interface Landscape {
  summary: string;
  clusters: Cluster[];
  relationships: Relationship[];
  tensions: string[];
  open_problems: string[];
}

export interface LandscapeDoc {
  id: string;
  topic: string;
  created_at: number;
  landscape: Landscape;
  papers: Paper[];
}

export interface LandscapeSummary {
  id: string;
  topic: string;
  created_at: number;
  summary: string;
  n: number;
}

export async function startSearch(topic: string): Promise<{ job_id: string }> {
  const r = await fetch(`${API_BASE}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic }),
  });
  if (!r.ok) throw new Error(`search failed: ${r.status}`);
  return r.json();
}

// Subscribe to a job's SSE progress stream. Returns an unsubscribe fn.
export function streamJob(
  jobId: string,
  onUpdate: (s: JobSnapshot) => void,
  onEnd: (s: JobSnapshot) => void
): () => void {
  const es = new EventSource(`${API_BASE}/api/jobs/${jobId}/stream`);
  es.onmessage = (e) => onUpdate(JSON.parse(e.data));
  es.addEventListener("end", (e) => {
    onEnd(JSON.parse((e as MessageEvent).data));
    es.close();
  });
  es.onerror = () => es.close();
  return () => es.close();
}

export async function getLandscape(id: string): Promise<LandscapeDoc> {
  const r = await fetch(`${API_BASE}/api/landscapes/${id}`);
  if (!r.ok) throw new Error(`landscape ${id} not found`);
  return r.json();
}

export async function listLandscapes(): Promise<LandscapeSummary[]> {
  const r = await fetch(`${API_BASE}/api/landscapes`);
  if (!r.ok) return [];
  return (await r.json()).landscapes;
}

export async function health(): Promise<any> {
  const r = await fetch(`${API_BASE}/api/health`);
  return r.json();
}
