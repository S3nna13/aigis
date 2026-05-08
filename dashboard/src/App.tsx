import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { Overview } from "./pages/Overview";
import { Evals } from "./pages/Evals";
import { Guardrails } from "./pages/Guardrails";
import Reports from "./pages/Reports";
import { GuardrailLogs } from "./pages/GuardrailLogs";
import { SettingsPage } from "./pages/Settings";
import { AuditPage } from "./pages/Audit";
import type { EvalRun } from "./api";
import { loadLocalResults, saveLocalResults } from "./api";

export type Page =
  | "overview"
  | "evals"
  | "guardrails"
  | "reports"
  | "guardlogs"
  | "settings"
  | "audit";

export function App() {
  const [currentPage, setCurrentPage] = useState<Page>("overview");
  const [evalRuns, setEvalRuns] = useState<EvalRun[]>(() => loadLocalResults());

  const addEvalRun = (run: EvalRun) => {
    const updated = [run, ...evalRuns];
    setEvalRuns(updated);
    saveLocalResults(updated);
  };

  const removeEvalRun = (id: string) => {
    setEvalRuns((prev) => prev.filter((r) => r.id !== id));
    saveLocalResults(evalRuns.filter((r) => r.id !== id));
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {currentPage === "overview" && <Overview evalRuns={evalRuns} />}
          {currentPage === "evals" && (
            <Evals evalRuns={evalRuns} onDelete={removeEvalRun} />
          )}
          {currentPage === "guardrails" && <Guardrails />}
          {currentPage === "reports" && <Reports />}
          {currentPage === "guardlogs" && <GuardrailLogs />}
          {currentPage === "settings" && <SettingsPage />}
          {currentPage === "audit" && <AuditPage />}
        </div>
      </main>
    </div>
  );
}
