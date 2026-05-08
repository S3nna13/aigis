import { useEffect, useState } from "react";
import { ScrollText, Search, ChevronDown } from "lucide-react";

interface AuditEntry {
  timestamp: string;
  event: string;
  source: string;
  data: Record<string, any>;
}

export function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const resp = await fetch("/api/audit?limit=100");
        if (resp.ok) {
          const data = await resp.json();
          setEntries(data.entries || []);
        }
      } catch {
        setEntries([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filtered = entries.filter(
    (e) =>
      e.event.toLowerCase().includes(search.toLowerCase()) ||
      e.source.toLowerCase().includes(search.toLowerCase())
  );

  const eventColors: Record<string, string> = {
    "guardrail.triggered": "bg-red-950/60 text-red-300",
    "guardrail.passed": "bg-emerald-950/60 text-emerald-300",
    "eval.started": "bg-blue-950/60 text-blue-300",
    "eval.completed": "bg-indigo-950/60 text-indigo-300",
    "webhook.dispatched": "bg-amber-950/60 text-amber-300",
  };

  const badgeColor = (event: string) =>
    eventColors[event] || "bg-slate-800 text-slate-300";

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Audit Log</h1>
          <p className="text-indigo-300/70 mt-1">Immutable record of all system events</p>
        </div>
      </div>

      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-indigo-400" />
        <input
          type="text"
          placeholder="Search events or sources..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-indigo-950/60 border border-indigo-900/50 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-indigo-400/50 focus:outline-none focus:border-indigo-500/50"
        />
      </div>

      {loading ? (
        <div className="text-center py-16 text-indigo-300/50">
          <ScrollText className="w-8 h-8 mx-auto mb-3 animate-pulse" />
          <p>Loading audit log...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-indigo-300/50">
          <ScrollText className="w-8 h-8 mx-auto mb-3 opacity-50" />
          <p>No audit entries found.</p>
          <p className="text-sm mt-2">
            Run <code className="bg-indigo-900/50 px-2 py-1 rounded text-indigo-200">aigis guard --all</code> to generate entries.
          </p>
        </div>
      ) : (
        <div className="bg-indigo-950/30 border border-indigo-900/40 rounded-xl overflow-hidden">
          <div className="divide-y divide-indigo-900/30">
            {filtered.map((entry, i) => (
              <div key={i} className="px-5 py-4">
                <button
                  onClick={() => setExpanded(expanded === `${i}` ? null : `${i}`)}
                  className="w-full flex items-start gap-3 text-left"
                >
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 mt-0.5 ${badgeColor(
                      entry.event
                    )}`}
                  >
                    {entry.event}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 text-xs text-indigo-300/60">
                      <span>{new Date(entry.timestamp).toLocaleString()}</span>
                      <span className="font-mono text-indigo-400/60">{entry.source}</span>
                    </div>
                  </div>
                  <ChevronDown
                    className={`w-3.5 h-3.5 text-indigo-400 flex-shrink-0 transition-transform ${
                      expanded === `${i}` ? "rotate-180" : ""
                    }`}
                  />
                </button>
                {expanded === `${i}` && entry.data && (
                  <pre className="mt-3 text-xs text-indigo-200/70 bg-indigo-950/60 rounded-lg p-3 overflow-x-auto">
                    {JSON.stringify(entry.data, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}