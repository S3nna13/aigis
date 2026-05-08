import { useState } from "react";
import { Search, CheckCircle, XCircle, HelpCircle, ChevronRight } from "lucide-react";
import type { EvalRun } from "../api";
import { sanitize } from "../api";
import { EvalDetail } from "./EvalDetail";

interface EvalsProps {
  evalRuns: EvalRun[];
  onDelete?: (id: string) => void;
}

export function Evals({ evalRuns, onDelete }: EvalsProps) {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<EvalRun | null>(null);

  const filtered = evalRuns.filter((r) =>
    r.name.toLowerCase().includes(search.toLowerCase())
  );

  if (selected) {
    return (
      <EvalDetail
        run={selected}
        onBack={() => setSelected(null)}
        onDelete={(id) => {
          onDelete?.(id);
          setSelected(null);
        }}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Evaluations</h1>
          <p className="text-indigo-300/70 mt-1">View and analyze all eval runs</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-indigo-400" />
          <input
            type="text"
            placeholder="Search evals..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-indigo-950/60 border border-indigo-900/50 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-indigo-400/50 focus:outline-none focus:border-indigo-500/50 w-64"
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-16 text-indigo-300/50">
          <p className="text-lg">No evaluations found</p>
          <p className="text-sm mt-2">Run your first evaluation using the CLI</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((run) => {
            const Icon =
              run.summary.pass_rate >= 0.8
                ? CheckCircle
                : run.summary.pass_rate >= 0.5
                ? HelpCircle
                : XCircle;
            const iconColor =
              run.summary.pass_rate >= 0.8
                ? "text-emerald-400"
                : run.summary.pass_rate >= 0.5
                ? "text-amber-400"
                : "text-red-400";

            return (
              <button
                key={run.id}
                onClick={() => setSelected(run)}
                className="w-full bg-indigo-950/40 border border-indigo-900/50 rounded-xl p-5 hover:border-indigo-700/50 transition-all text-left flex items-center gap-4"
              >
                <Icon className={`w-5 h-5 flex-shrink-0 ${iconColor}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1.5">
                    <h3 className="font-semibold text-white truncate">{sanitize(run.name)}</h3>
                    <span className="text-xs text-indigo-400 flex-shrink-0 ml-3">
                      {run.summary.total} tests
                    </span>
                  </div>
                  <div className="flex items-center gap-5 text-xs text-indigo-300/70">
                    <span>
                      Score:{" "}
                      <span className="text-white font-medium">
                        {(run.summary.avg_score * 100).toFixed(0)}%
                      </span>
                    </span>
                    <span>
                      Pass:{" "}
                      <span className="text-white font-medium">
                        {run.summary.passed}/{run.summary.total}
                      </span>
                    </span>
                    <span className="text-indigo-400/50">
                      {new Date(run.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-indigo-400/50 flex-shrink-0" />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}