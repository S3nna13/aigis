import { useState } from "react";
import { ArrowLeft, CheckCircle, XCircle, Clock, Zap, Trash2 } from "lucide-react";
import type { EvalRun, EvalResult } from "../api";
import { sanitize, deleteEval } from "../api";

interface EvalDetailProps {
  run: EvalRun;
  onBack: () => void;
  onDelete: (id: string) => void;
}

export function EvalDetail({ run, onBack, onDelete }: EvalDetailProps) {
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleDelete = async () => {
    await deleteEval(run.id);
    onDelete(run.id);
  };

  const passCount = run.results.filter((r) => r.passed === true).length;
  const failCount = run.results.filter((r) => r.passed === false).length;
  const nullCount = run.results.filter((r) => r.passed == null).length;

  return (
    <div>
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-indigo-300/70 hover:text-indigo-200 text-sm mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Evaluations
      </button>

      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">{sanitize(run.name)}</h1>
          <div className="flex items-center gap-4 mt-2 text-sm text-indigo-300/70">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {new Date(run.timestamp).toLocaleString()}
            </span>
            {run.summary.latency_ms != null && (
              <span className="flex items-center gap-1">
                <Zap className="w-3.5 h-3.5" />
                {run.summary.latency_ms.toFixed(0)}ms
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-3">
          {confirmDelete ? (
            <div className="flex items-center gap-2">
              <span className="text-sm text-red-400">Delete this eval?</span>
              <button
                onClick={handleDelete}
                className="px-3 py-1.5 text-xs bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Confirm
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="px-3 py-1.5 text-xs bg-indigo-800 hover:bg-indigo-700 text-indigo-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-red-400 bg-red-950/40 hover:bg-red-900/40 border border-red-800/40 rounded-lg transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          { label: "Total", value: run.results.length, color: "from-blue-500 to-indigo-600" },
          { label: "Passed", value: passCount, color: "from-emerald-500 to-teal-600" },
          { label: "Failed", value: failCount, color: "from-red-500 to-rose-600" },
          { label: "Unknown", value: nullCount, color: "from-slate-500 to-gray-600" },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl p-4">
            <span className="text-xs text-indigo-300/70">{label}</span>
            <p className="text-2xl font-bold text-white mt-1">{value}</p>
            <div className={`mt-2 h-1 rounded-full bg-gradient-to-r ${color} opacity-60`} />
          </div>
        ))}
      </div>

      <div className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-indigo-900/50">
          <h2 className="text-sm font-semibold text-indigo-200">Test Results</h2>
        </div>
        <div className="divide-y divide-indigo-900/30">
          {run.results.map((result: EvalResult, i: number) => (
            <ResultRow key={i} result={result} input={run.summary} />
          ))}
        </div>
      </div>
    </div>
  );
}

function ResultRow({ result, input }: { result: EvalResult; input: any }) {
  const [expanded, setExpanded] = useState(false);
  const passed = result.passed;
  const Icon = passed === true ? CheckCircle : passed === false ? XCircle : Clock;
  const iconColor =
    passed === true
      ? "text-emerald-400"
      : passed === false
      ? "text-red-400"
      : "text-slate-400";
  const scorePct = (result.score * 100).toFixed(0);

  return (
    <div className="px-6 py-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 text-left"
      >
        <Icon className={`w-4 h-4 flex-shrink-0 ${iconColor}`} />
        <span className="text-sm font-medium text-white flex-1">{sanitize(result.name)}</span>
        <span
          className={`text-xs px-2 py-0.5 rounded-full ${
            passed === true
              ? "bg-emerald-950/60 text-emerald-400"
              : passed === false
              ? "bg-red-950/60 text-red-400"
              : "bg-slate-800 text-slate-400"
          }`}
        >
          {passed === true ? "PASS" : passed === false ? "FAIL" : "N/A"} {scorePct}%
        </span>
      </button>

      {expanded && (
        <div className="mt-3 pl-7 space-y-2 text-xs">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-indigo-400">Score: </span>
              <span className="text-white">{result.score.toFixed(3)}</span>
            </div>
            {input && (
              <div>
                <span className="text-indigo-400">Input: </span>
                <span className="text-white break-all">{sanitize(String(input))}</span>
              </div>
            )}
          </div>
          {result.reason && (
            <div>
              <span className="text-indigo-400">Reason: </span>
              <span className="text-white/80">{sanitize(result.reason)}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}