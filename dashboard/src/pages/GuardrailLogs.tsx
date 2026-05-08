import { useEffect, useState } from "react";
import { Shield, Trash2, Search, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { fetchGuardrailLogs, deleteGuardrailLog } from "../api";
import type { GuardrailLog, GuardrailCheck } from "../api";
import { sanitize } from "../api";

export function GuardrailLogs() {
  const [logs, setLogs] = useState<GuardrailLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchGuardrailLogs().then((data) => {
      setLogs(data);
      setLoading(false);
    });
  }, []);

  const handleDelete = async (id: string) => {
    await deleteGuardrailLog(id);
    setLogs((prev) => prev.filter((l) => l.id !== id));
  };

  const filtered = logs.filter((log) =>
    log.text.toLowerCase().includes(search.toLowerCase())
  );

  const passCount = filtered.filter((l) => l.passed).length;
  const failCount = filtered.filter((l) => !l.passed).length;

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Guardrail Logs</h1>
          <p className="text-indigo-300/70 mt-1">History of all guardrail checks</p>
        </div>
        <div className="flex gap-4">
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle className="w-3.5 h-3.5" />
              {passCount} passed
            </span>
            <span className="flex items-center gap-1.5 text-red-400">
              <XCircle className="w-3.5 h-3.5" />
              {failCount} triggered
            </span>
          </div>
        </div>
      </div>

      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-indigo-400" />
        <input
          type="text"
          placeholder="Search by text..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-indigo-950/60 border border-indigo-900/50 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-indigo-400/50 focus:outline-none focus:border-indigo-500/50"
        />
      </div>

      {loading ? (
        <div className="text-center py-16 text-indigo-300/50">
          <Shield className="w-8 h-8 mx-auto mb-3 animate-pulse" />
          <p>Loading guardrail logs...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-indigo-300/50">
          <Shield className="w-8 h-8 mx-auto mb-3 opacity-50" />
          <p>No guardrail checks yet.</p>
          <p className="text-sm mt-2">Use the Guardrail Check panel on Overview to run a check.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((log) => (
            <LogCard key={log.id} log={log} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}

function LogCard({
  log,
  onDelete,
}: {
  log: GuardrailLog;
  onDelete: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const Icon = log.passed ? CheckCircle : XCircle;
  const iconColor = log.passed ? "text-emerald-400" : "text-red-400";

  const triggeredRails = log.results.filter((r) => !r.passed);

  return (
    <div className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start gap-3 p-5 text-left"
      >
        <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${iconColor}`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm text-white line-clamp-2">{sanitize(log.text)}</p>
          <div className="flex items-center gap-3 mt-2 text-xs text-indigo-300/60">
            <span>{new Date(log.timestamp).toLocaleString()}</span>
            {triggeredRails.length > 0 && (
              <span className="text-amber-400">
                {triggeredRails.length} rail{triggeredRails.length > 1 ? "s" : ""} triggered
              </span>
            )}
          </div>
        </div>
        <span
          className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${
            log.passed
              ? "bg-emerald-950/60 text-emerald-400"
              : "bg-red-950/60 text-red-400"
          }`}
        >
          {log.passed ? "PASS" : "TRIGGERED"}
        </span>
      </button>

      {expanded && (
        <div className="px-5 pb-5 border-t border-indigo-900/30">
          <div className="pt-4 space-y-2">
            {log.results.map((r) => (
              <RailResultRow key={r.name} result={r} />
            ))}
          </div>
          <div className="flex justify-end mt-4">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(log.id);
              }}
              className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete log
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function RailResultRow({ result }: { result: GuardrailCheck }) {
  const Icon =
    result.severity === "critical"
      ? XCircle
      : result.severity === "warning"
      ? AlertTriangle
      : CheckCircle;
  const iconColor =
    result.severity === "critical"
      ? "text-red-400"
      : result.severity === "warning"
      ? "text-amber-400"
      : "text-emerald-400";
  const labelColor = result.passed
    ? "bg-emerald-950/60 text-emerald-400"
    : "bg-red-950/60 text-red-400";

  return (
    <div className="flex items-start gap-2.5">
      <Icon className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${iconColor}`} />
      <span className="text-xs text-indigo-200 capitalize flex-1">
        {result.name.replace(/_/g, " ")}
      </span>
      <span className={`text-xs px-1.5 py-0.5 rounded ${labelColor}`}>
        {result.passed ? "PASS" : "FAIL"} {result.score > 0 ? `${(result.score * 100).toFixed(0)}%` : ""}
      </span>
    </div>
  );
}