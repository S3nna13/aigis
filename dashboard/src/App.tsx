import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { Overview } from "./pages/Overview";
import { Evals } from "./pages/Evals";
import { Guardrails } from "./pages/Guardrails";
import type { EvalRun } from "./api";
import { loadLocalResults, saveLocalResults } from "./api";

export type Page = "overview" | "evals" | "guardrails" | "reports";

export function App() {
  const [currentPage, setCurrentPage] = useState<Page>("overview");
  const [evalRuns, setEvalRuns] = useState<EvalRun[]>(() => loadLocalResults());

  const addEvalRun = (run: EvalRun) => {
    const updated = [run, ...evalRuns];
    setEvalRuns(updated);
    saveLocalResults(updated);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {currentPage === "overview" && <Overview evalRuns={evalRuns} />}
          {currentPage === "evals" && <Evals evalRuns={evalRuns} />}
          {currentPage === "guardrails" && <Guardrails />}
        </div>
      </main>
    </div>
  );
}
