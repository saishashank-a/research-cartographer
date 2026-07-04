"use client";
import { useEffect, useRef, useState } from "react";
import {
  startSearch,
  streamJob,
  getLandscape,
  listLandscapes,
  health,
  JobSnapshot,
  LandscapeDoc,
  LandscapeSummary,
} from "@/lib/api";
import PipelineProgress from "@/components/PipelineProgress";
import LandscapeView from "@/components/LandscapeView";

const SUGGESTIONS = [
  "retrieval augmented generation",
  "diffusion policy learning",
  "mixture of experts",
  "mechanistic interpretability",
];

export default function Home() {
  const [topic, setTopic] = useState("");
  const [job, setJob] = useState<JobSnapshot | null>(null);
  const [doc, setDoc] = useState<LandscapeDoc | null>(null);
  const [library, setLibrary] = useState<LandscapeSummary[]>([]);
  const [busy, setBusy] = useState(false);
  const [ollamaOk, setOllamaOk] = useState<boolean | null>(null);
  const [modelName, setModelName] = useState("");
  const unsubRef = useRef<null | (() => void)>(null);

  async function refreshLibrary() {
    setLibrary(await listLandscapes());
  }

  useEffect(() => {
    health()
      .then((h) => {
        setOllamaOk(h?.ollama?.ok ?? false);
        setModelName(h?.model ?? "");
      })
      .catch(() => setOllamaOk(false));
    refreshLibrary();
    return () => unsubRef.current?.();
  }, []);

  async function run(t: string) {
    const q = t.trim();
    if (!q || busy) return;
    setBusy(true);
    setDoc(null);
    setJob(null);
    unsubRef.current?.();
    try {
      const { job_id } = await startSearch(q);
      unsubRef.current = streamJob(
        job_id,
        (s) => setJob(s),
        async (final) => {
          setJob(final);
          setBusy(false);
          if (final.status === "done" && final.landscape_id) {
            setDoc(await getLandscape(final.landscape_id));
            refreshLibrary();
          }
        }
      );
    } catch (e) {
      setBusy(false);
      setJob({
        id: "err",
        topic: q,
        status: "error",
        landscape_id: null,
        error: String(e),
        version: 0,
        stages: [],
      });
    }
  }

  async function openSaved(id: string) {
    unsubRef.current?.();
    setJob(null);
    setBusy(false);
    setDoc(await getLandscape(id));
  }

  return (
    <div className="mx-auto max-w-7xl px-5 py-10">
      {/* header */}
      <header className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="bg-gradient-to-r from-white via-indigo-200 to-cyan-200 bg-clip-text text-3xl font-bold tracking-tight text-transparent">
            Research Cartographer
          </h1>
          <p className="mt-1 max-w-xl text-sm text-gray-400">
            Map an entire ML research field from a single search. arXiv retrieves;
            a local LLM reads, ranks, and synthesizes a living research landscape.
          </p>
        </div>
        <div className="text-right text-xs">
          <div
            className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 ${
              ollamaOk === null
                ? "border-white/10 text-gray-500"
                : ollamaOk
                ? "border-emerald-400/30 text-emerald-300"
                : "border-rose-400/30 text-rose-300"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                ollamaOk ? "bg-emerald-400" : ollamaOk === false ? "bg-rose-500" : "bg-gray-500"
              }`}
            />
            {ollamaOk === null ? "checking…" : ollamaOk ? `Ollama · ${modelName}` : "Ollama offline"}
          </div>
        </div>
      </header>

      {/* search */}
      <div className="card mb-4 p-2">
        <div className="flex items-center gap-2">
          <span className="pl-3 text-gray-500">⌕</span>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run(topic)}
            placeholder="Enter an ML topic in plain English…"
            className="flex-1 bg-transparent px-2 py-2.5 text-sm text-gray-100 placeholder-gray-500 outline-none"
          />
          <button
            onClick={() => run(topic)}
            disabled={busy || !topic.trim()}
            className="rounded-lg bg-gradient-to-r from-accent to-indigo-500 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-accent/20 transition enabled:hover:brightness-110 disabled:opacity-40"
          >
            {busy ? "Mapping…" : "Map field"}
          </button>
        </div>
      </div>
      <div className="mb-8 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => {
              setTopic(s);
              run(s);
            }}
            disabled={busy}
            className="chip glass-hover disabled:opacity-40"
          >
            {s}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* main column */}
        <div className="lg:col-span-3">
          {job && job.status !== "done" && <PipelineProgress job={job} />}
          {job && job.status === "done" && !doc && <PipelineProgress job={job} />}
          {doc && <LandscapeView doc={doc} />}
          {!job && !doc && (
            <div className="card flex min-h-[300px] flex-col items-center justify-center p-10 text-center">
              <div className="mb-3 text-4xl opacity-30">🗺️</div>
              <p className="max-w-sm text-sm text-gray-400">
                Search any ML topic and watch a four-stage pipeline — retrieve, rerank,
                extract, synthesize — build an interactive research landscape.
              </p>
            </div>
          )}
        </div>

        {/* reading-map sidebar (grows over time) */}
        <aside className="lg:col-span-1">
          <div className="card sticky top-6 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Your reading map
              </h3>
              <span className="chip">{library.length}</span>
            </div>
            {library.length === 0 ? (
              <p className="text-xs text-gray-500">
                Saved landscapes accumulate here as you explore more topics.
              </p>
            ) : (
              <div className="space-y-2">
                {library.map((l) => (
                  <button
                    key={l.id}
                    onClick={() => openSaved(l.id)}
                    className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                      doc?.id === l.id
                        ? "border-accent/50 bg-accent/10"
                        : "border-white/10 hover:bg-white/5"
                    }`}
                  >
                    <div className="truncate text-sm font-medium text-gray-100">{l.topic}</div>
                    <div className="mt-0.5 flex items-center gap-2 text-xs text-gray-500">
                      <span>{l.n} papers</span>
                      <span>·</span>
                      <span>{new Date(l.created_at * 1000).toLocaleDateString()}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </aside>
      </div>

      <footer className="mt-12 border-t border-white/5 pt-5 text-center text-xs text-gray-600">
        FastAPI + arXiv + cross-encoder + local LLM (Ollama) · Next.js + Tailwind
      </footer>
    </div>
  );
}
