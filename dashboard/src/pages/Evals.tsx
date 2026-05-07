import { useState } from "react";
import { Search, Download, CheckCircle, XCircle, HelpCircle } from "lucide-react";
import type { EvalRun } from "../api";

interface EvalsProps {
  evalRuns: EvalRun[];
}

export function Evals({ evalRuns }: EvalsProps) {
  const [search, setSearch] = useState("");

  const filtered = evalRuns.filter((r) =>
    r.name.toLowerCase().includes(search.toLowerCase())
  );

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
        <div className="space-y-4">
          {filtered.map((run) => {
            const Icon = run.summary.pass_rate >= 0.8
              ? CheckCircle : run.summary.pass_rate >= 0.5
              ? HelpCircle : XCircle;
            const iconColor = run.summary.pass_rate >= 0.8
              ? "text-emerald-400" : run.summary.pass_rate >= 0.5
              ? "text-amber-400" : "text-red-400";

            return (
              <div
                key={run.id}
                className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl p-5 hover:border-indigo-700/50 transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Icon className={`w-5 h-5 ${iconColor}`} />
                    <h3 className="font-semibold text-white">{run.name}</h3>
                  </div>
                    <span className="text-xs text-indigo-400">{run.summary.total} tests</span>
                </div>
                <div className="flex gap-6 text-sm">
                  <span className="text-indigo-300/70">
                    Score: <span className="text-white font-medium">{(run.summary.avg_score * 100).toFixed(0)}%</span>
                  </span>
                  <span className="text-indigo-300/70">
                    Pass Rate: <span className="text-white font-medium">{(run.summary.pass_rate * 100).toFixed(0)}%</span>
                  </span>
                  <span className="text-indigo-300/70">
                    Tests: <span className="text-white font-medium">{run.results.length}</span>
                  </span>
                  <span className="text-indigo-300/70 text-xs ml-auto">
                    {new Date(run.timestamp).toLocaleDateString()}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
