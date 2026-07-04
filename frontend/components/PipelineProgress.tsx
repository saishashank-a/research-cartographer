"use client";
import { JobSnapshot, Stage } from "@/lib/api";

const STAGE_META: Record<string, { label: string; blurb: string; icon: string }> = {
  retrieve: { label: "Retrieve", blurb: "arXiv pulls candidate papers", icon: "◎" },
  rerank: { label: "Rerank", blurb: "Cross-encoder scores relevance", icon: "⇅" },
  extract: { label: "Extract", blurb: "LLM reads each paper", icon: "❏" },
  synthesize: { label: "Synthesize", blurb: "Cross-paper landscape", icon: "✦" },
};

function dot(status: Stage["status"]) {
  if (status === "done") return "bg-emerald-400";
  if (status === "running") return "bg-accent-glow animate-pulse-ring";
  if (status === "error") return "bg-rose-500";
  return "bg-white/20";
}

export default function PipelineProgress({ job }: { job: JobSnapshot }) {
  return (
    <div className="card p-5 animate-fade-up">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-300">
          Mapping <span className="text-accent-glow">“{job.topic}”</span>
        </h3>
        <span className="chip">
          {job.status === "done" ? "complete" : job.status === "error" ? "failed" : "running"}
        </span>
      </div>

      <div className="space-y-1">
        {job.stages.map((s, i) => {
          const meta = STAGE_META[s.name] ?? { label: s.name, blurb: "", icon: "•" };
          const active = s.status === "running";
          return (
            <div key={s.name}>
              <div
                className={`flex items-start gap-3 rounded-lg px-3 py-2.5 transition ${
                  active ? "bg-white/[0.04]" : ""
                }`}
              >
                <div className="mt-0.5 flex flex-col items-center">
                  <span className={`h-2.5 w-2.5 rounded-full ${dot(s.status)}`} />
                  {i < job.stages.length - 1 && (
                    <span
                      className={`mt-1 h-8 w-px ${
                        s.status === "done" ? "bg-emerald-400/40" : "bg-white/10"
                      }`}
                    />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-sm font-medium ${
                        s.status === "pending" ? "text-gray-500" : "text-gray-100"
                      }`}
                    >
                      <span className="mr-1.5 text-accent-glow">{meta.icon}</span>
                      {meta.label}
                    </span>
                    {s.status === "running" && s.progress > 0 && (
                      <span className="text-xs tabular-nums text-accent-glow">
                        {Math.round(s.progress * 100)}%
                      </span>
                    )}
                  </div>
                  <p className="truncate text-xs text-gray-400">
                    {s.detail || meta.blurb}
                  </p>
                  {(active || (s.status === "done" && s.progress < 1)) && (
                    <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-white/10">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-accent to-cyan transition-all duration-500"
                        style={{ width: `${Math.max(6, s.progress * 100)}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {job.error && (
        <div className="mt-3 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
          {job.error}
        </div>
      )}
    </div>
  );
}
