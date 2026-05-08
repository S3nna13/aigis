import { useState } from "react";
import { Shield, ChevronDown, CheckCircle, XCircle, AlertTriangle, Loader2 } from "lucide-react";
import { checkGuardrails } from "../api";
import type { GuardrailCheck } from "../api";

const RAIL_OPTIONS = [
  { key: "jailbreak", label: "Jailbreak" },
  { key: "toxic", label: "Toxicity" },
  { key: "toxicity_filter", label: "Toxicity Filter" },
  { key: "pii", label: "PII" },
  { key: "injection", label: "Prompt Injection" },
  { key: "secrets", label: "Secrets" },
  { key: "context", label: "Context Length" },
  { key: "rag_poisoning", label: "RAG Poisoning" },
  { key: "structured_output", label: "Structured Output" },
  { key: "constitutional", label: "Constitutional" },
  { key: "factual", label: "Factual Consistency" },
  { key: "hallucination", label: "Hallucination" },
];

export function GuardCheckPanel() {
  const [text, setText] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [results, setResults] = useState<GuardrailCheck[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  const toggleRail = (key: string) => {
    setSelected((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const handleCheck = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const log = await checkGuardrails(text, selected.length > 0 ? selected : undefined);
      setResults(log.results);
    } catch (err: any) {
      setError(err.message || "Check failed");
    } finally {
      setLoading(false);
    }
  };

  const passedCount = results?.filter((r) => r.passed).length ?? 0;
  const totalCount = results?.length ?? 0;

  return (
    <div className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-indigo-900/20 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Shield className="w-5 h-5 text-indigo-400" />
          <div className="text-left">
            <h2 className="text-sm font-semibold text-white">Guardrail Check</h2>
            <p className="text-xs text-indigo-300/60">Test text against AI safety rails</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {results && (
            <span
              className={`text-xs px-2 py-0.5 rounded-full ${
                passedCount === totalCount
                  ? "bg-emerald-950/60 text-emerald-400"
                  : "bg-amber-950/60 text-amber-400"
              }`}
            >
              {passedCount}/{totalCount} passed
            </span>
          )}
          <ChevronDown
            className={`w-4 h-4 text-indigo-400 transition-transform ${open ? "rotate-180" : ""}`}
          />
        </div>
      </button>

      {open && (
        <div className="px-6 pb-6 space-y-4">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter text to check against guardrails..."
            rows={3}
            className="w-full bg-indigo-950/80 border border-indigo-800/50 rounded-lg px-4 py-3 text-sm text-white placeholder-indigo-400/40 focus:outline-none focus:border-indigo-500/50 resize-none"
          />

          <div>
            <p className="text-xs text-indigo-300/60 mb-2">Rails to check:</p>
            <div className="flex flex-wrap gap-2">
              {RAIL_OPTIONS.map(({ key, label }) => {
                const active = selected.includes(key);
                return (
                  <button
                    key={key}
                    onClick={() => toggleRail(key)}
                    className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                      active
                        ? "bg-indigo-600/30 border-indigo-500/50 text-indigo-200"
                        : "bg-indigo-950/40 border-indigo-800/40 text-indigo-300/60 hover:border-indigo-700/40"
                    }`}
                  >
                    {label}
                  </button>
                );
              })}
              <button
                onClick={() => setSelected([])}
                className="text-xs px-2.5 py-1 rounded-full bg-indigo-950/40 border border-indigo-800/40 text-indigo-400/60 hover:border-indigo-700/40 transition-colors"
              >
                All
              </button>
            </div>
          </div>

          <button
            onClick={handleCheck}
            disabled={loading || !text.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Checking...
              </>
            ) : (
              <>
                <Shield className="w-4 h-4" />
                Check Guardrails
              </>
            )}
          </button>

          {error && (
            <p className="text-xs text-red-400 bg-red-950/40 border border-red-900/40 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          {results && (
            <div className="space-y-2">
              {results.map((r) => (
                <ResultRow key={r.name} result={r} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ResultRow({ result }: { result: GuardrailCheck }) {
  const [expanded, setExpanded] = useState(false);
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
  const bgColor =
    result.severity === "critical"
      ? "bg-red-950/30 border-red-900/40"
      : result.severity === "warning"
      ? "bg-amber-950/30 border-amber-900/40"
      : "bg-emerald-950/20 border-emerald-900/30";

  return (
    <div
      className={`border rounded-lg overflow-hidden ${bgColor}`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2.5 px-3 py-2.5"
      >
        <Icon className={`w-4 h-4 flex-shrink-0 ${iconColor}`} />
        <span className="text-sm text-white flex-1 text-left font-medium capitalize">
          {result.name.replace(/_/g, " ")}
        </span>
        <span
          className={`text-xs px-1.5 py-0.5 rounded ${
            result.passed
              ? "bg-emerald-900/50 text-emerald-300"
              : "bg-red-900/50 text-red-300"
          }`}
        >
          {result.passed ? "PASS" : "FAIL"}
        </span>
        <ChevronDown
          className={`w-3.5 h-3.5 text-indigo-400 transition-transform ${expanded ? "rotate-180" : ""}`}
        />
      </button>
      {expanded && result.reason && (
        <div className="px-3 pb-3 pt-0 text-xs text-indigo-200/70">
          {result.reason}
        </div>
      )}
    </div>
  );
}