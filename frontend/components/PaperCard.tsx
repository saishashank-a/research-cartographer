"use client";
import { useState } from "react";
import { Paper } from "@/lib/api";

export default function PaperCard({
  paper,
  index,
  matchPct,
}: {
  paper: Paper;
  index: number;
  matchPct?: number; // 0..1 relevance for display, normalized across the set
}) {
  const [open, setOpen] = useState(false);
  const ex = paper.extraction || ({} as Paper["extraction"]);
  const score = matchPct ?? paper.rerank_score ?? 0;

  return (
    <div className="card glass-hover p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="mb-1 flex items-center gap-2">
            <span className="text-xs font-mono text-gray-500">[{index}]</span>
            {score > 0 && (
              <span
                className="chip"
                title="cross-encoder relevance"
                style={{
                  borderColor: `rgba(99,102,241,${0.2 + score * 0.5})`,
                  color: "#c7d2fe",
                }}
              >
                {(score * 100).toFixed(0)}% match
              </span>
            )}
            <span className="text-xs text-gray-500">{paper.published}</span>
          </div>
          <a
            href={paper.abs_url}
            target="_blank"
            rel="noreferrer"
            className="text-sm font-medium leading-snug text-gray-100 hover:text-accent-glow"
          >
            {paper.title}
          </a>
          <p className="mt-0.5 truncate text-xs text-gray-500">
            {paper.authors.slice(0, 4).join(", ")}
            {paper.authors.length > 4 ? " et al." : ""}
          </p>
        </div>
        <button
          onClick={() => setOpen((v) => !v)}
          className="shrink-0 rounded-md border border-white/10 px-2 py-1 text-xs text-gray-300 transition hover:bg-white/5"
        >
          {open ? "Hide" : "Card"}
        </button>
      </div>

      {ex.keywords?.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {ex.keywords.map((k) => (
            <span key={k} className="chip">
              {k}
            </span>
          ))}
        </div>
      )}

      {open && (
        <div className="mt-3 space-y-2 border-t border-white/10 pt-3 text-xs animate-fade-up">
          {(
            [
              ["Problem", ex.problem],
              ["Method", ex.method],
              ["Results", ex.results],
              ["Contribution", ex.contribution],
            ] as [string, string][]
          ).map(([label, val]) =>
            val ? (
              <div key={label}>
                <span className="font-semibold text-accent-glow">{label}. </span>
                <span className="text-gray-300">{val}</span>
              </div>
            ) : null
          )}
          <div className="flex gap-3 pt-1">
            <a href={paper.pdf_url} target="_blank" rel="noreferrer" className="text-cyan hover:underline">
              PDF ↗
            </a>
            <a href={paper.abs_url} target="_blank" rel="noreferrer" className="text-cyan hover:underline">
              arXiv ↗
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
