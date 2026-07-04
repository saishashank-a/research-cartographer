"use client";
import { useState } from "react";
import { LandscapeDoc } from "@/lib/api";
import PaperCard from "./PaperCard";

const RELATION_COLOR: Record<string, string> = {
  "builds-on": "text-emerald-300 border-emerald-400/30",
  "competes-with": "text-rose-300 border-rose-400/30",
  complements: "text-cyan border-cyan/30",
  enables: "text-amber-300 border-amber-400/30",
};

const CLUSTER_HUES = [199, 262, 152, 32, 340, 220, 90];

export default function LandscapeView({ doc }: { doc: LandscapeDoc }) {
  const { landscape, papers } = doc;
  const [activeCluster, setActiveCluster] = useState<number | null>(null);

  // Cross-encoder scores for relevant papers cluster near 1.0, so raw values
  // all read as "100%". Min-max normalise across this set (mapped to 62-100%)
  // so the reranking order is actually visible on the cards.
  const scores = papers.map((p) => p.rerank_score ?? 0);
  const hi = Math.max(...scores, 0.0001);
  const lo = Math.min(...scores);
  const matchPct = (s: number) =>
    hi === lo ? 1 : 0.62 + 0.38 * ((s - lo) / (hi - lo));

  const shownPapers =
    activeCluster === null
      ? papers.map((p, i) => ({ p, i }))
      : landscape.clusters[activeCluster].paper_indices.map((i) => ({ p: papers[i], i }));

  return (
    <div className="animate-fade-up space-y-6">
      {/* header */}
      <div className="card p-6">
        <div className="mb-1 flex items-center gap-2">
          <span className="chip">landscape</span>
          <h2 className="text-lg font-semibold text-gray-100">{doc.topic}</h2>
          <span className="ml-auto text-xs text-gray-500">
            {papers.length} papers · {landscape.clusters.length} clusters
          </span>
        </div>
        {landscape.summary && (
          <p className="text-sm leading-relaxed text-gray-300">{landscape.summary}</p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* left: clusters + relationships + tensions + open problems */}
        <div className="space-y-6 lg:col-span-2">
          <div>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
              Thematic clusters
            </h3>
            <div className="space-y-2">
              <button
                onClick={() => setActiveCluster(null)}
                className={`w-full rounded-lg border px-3 py-2 text-left text-xs transition ${
                  activeCluster === null
                    ? "border-accent/50 bg-accent/10 text-gray-100"
                    : "border-white/10 text-gray-400 hover:bg-white/5"
                }`}
              >
                All papers ({papers.length})
              </button>
              {landscape.clusters.map((c, idx) => {
                const hue = CLUSTER_HUES[idx % CLUSTER_HUES.length];
                const active = activeCluster === idx;
                return (
                  <button
                    key={idx}
                    onClick={() => setActiveCluster(active ? null : idx)}
                    className={`w-full rounded-lg border px-3 py-2.5 text-left transition ${
                      active ? "bg-white/[0.06]" : "hover:bg-white/[0.03]"
                    }`}
                    style={{
                      borderColor: active
                        ? `hsl(${hue} 70% 60% / 0.6)`
                        : "rgba(255,255,255,0.08)",
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2 text-sm font-medium text-gray-100">
                        <span
                          className="h-2.5 w-2.5 rounded-sm"
                          style={{ background: `hsl(${hue} 70% 60%)` }}
                        />
                        {c.name}
                      </span>
                      <span className="text-xs text-gray-500">{c.paper_indices.length}</span>
                    </div>
                    {c.description && (
                      <p className="mt-1 text-xs leading-snug text-gray-400">{c.description}</p>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {landscape.relationships.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
                How clusters relate
              </h3>
              <div className="space-y-1.5">
                {landscape.relationships.map((r, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="rounded bg-white/5 px-2 py-1 text-gray-300">{r.from}</span>
                    <span
                      className={`rounded-full border px-2 py-0.5 ${
                        RELATION_COLOR[r.relation] ?? "text-gray-300 border-white/20"
                      }`}
                    >
                      {r.relation} →
                    </span>
                    <span className="rounded bg-white/5 px-2 py-1 text-gray-300">{r.to}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {landscape.tensions.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
                Tensions &amp; trade-offs
              </h3>
              <ul className="space-y-1.5">
                {landscape.tensions.map((t, i) => (
                  <li
                    key={i}
                    className="rounded-lg border border-amber-400/20 bg-amber-400/[0.06] px-3 py-2 text-xs leading-snug text-amber-100/90"
                  >
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {landscape.open_problems.length > 0 && (
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
                Open problems
              </h3>
              <ul className="space-y-1.5">
                {landscape.open_problems.map((o, i) => (
                  <li
                    key={i}
                    className="flex gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs leading-snug text-gray-300"
                  >
                    <span className="text-accent-glow">◇</span>
                    {o}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* right: reading map (papers) */}
        <div className="lg:col-span-3">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
            Reading map
            {activeCluster !== null && (
              <span className="ml-2 font-normal normal-case text-accent-glow">
                · {landscape.clusters[activeCluster].name}
              </span>
            )}
          </h3>
          <div className="space-y-3">
            {shownPapers.map(({ p, i }) => (
              <PaperCard
                key={p.arxiv_id}
                paper={p}
                index={i}
                matchPct={matchPct(p.rerank_score ?? 0)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
