import { useState } from "react";
import { Shield, AlertTriangle, CheckCircle, XCircle, Eye } from "lucide-react";

interface RailStatus {
  name: string;
  type: "input" | "output" | "retrieval" | "execution";
  status: "active" | "inactive" | "triggered";
  hits: number;
  lastTriggered: string | null;
}

const defaultRails: RailStatus[] = [
  { name: "JailbreakDetector", type: "input", status: "active", hits: 0, lastTriggered: null },
  { name: "ToxicityGuardrail", type: "input", status: "active", hits: 0, lastTriggered: null },
  { name: "ToxicityFilter", type: "input", status: "active", hits: 0, lastTriggered: null },
  { name: "PIIDetector", type: "input", status: "active", hits: 0, lastTriggered: null },
  { name: "PromptInjectionDetector", type: "input", status: "active", hits: 0, lastTriggered: null },
  { name: "SecretScanner", type: "input", status: "active", hits: 0, lastTriggered: null },
  { name: "ContextWindowGuard", type: "input", status: "active", hits: 0, lastTriggered: null },
  { name: "ConstitutionalCritique", type: "output", status: "active", hits: 0, lastTriggered: null },
  { name: "FactualConsistency", type: "output", status: "active", hits: 0, lastTriggered: null },
  { name: "HallucinationDetector", type: "output", status: "active", hits: 0, lastTriggered: null },
  { name: "RAGPoisoningDetector", type: "retrieval", status: "inactive", hits: 0, lastTriggered: null },
  { name: "StructuredOutputValidator", type: "output", status: "inactive", hits: 0, lastTriggered: null },
];

export function Guardrails() {
  const [rails] = useState<RailStatus[]>(defaultRails);

  const statusIcon = (status: RailStatus["status"]) => {
    switch (status) {
      case "active": return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case "triggered": return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      case "inactive": return <XCircle className="w-4 h-4 text-indigo-400/50" />;
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-2">Guardrails</h1>
      <p className="text-indigo-300/70 mb-8">Manage and monitor your AI safety guardrails</p>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-semibold text-white">Input Rails</h2>
          </div>
          <p className="text-sm text-indigo-300/70 mb-4">
            Applied to user input before it reaches the LLM
          </p>
          <div className="space-y-3">
            {rails.filter((r) => r.type === "input").map((rail) => (
              <div key={rail.name} className="flex items-center justify-between p-3 bg-indigo-950/60 rounded-lg border border-indigo-900/30">
                <div className="flex items-center gap-3">
                  {statusIcon(rail.status)}
                  <span className="text-sm text-white">{rail.name}</span>
                </div>
                <span className="text-xs text-indigo-400">{rail.hits} blocks</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Eye className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-semibold text-white">Output Rails</h2>
          </div>
          <p className="text-sm text-indigo-300/70 mb-4">
            Applied to LLM output before it reaches the user
          </p>
          <div className="space-y-3">
            {rails.filter((r) => r.type === "output").map((rail) => (
              <div key={rail.name} className="flex items-center justify-between p-3 bg-indigo-950/60 rounded-lg border border-indigo-900/30">
                <div className="flex items-center gap-3">
                  {statusIcon(rail.status)}
                  <span className="text-sm text-white">{rail.name}</span>
                </div>
                <span className="text-xs text-indigo-400">{rail.hits} blocks</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
