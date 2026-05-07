export interface EvalResult {
  name: string;
  score: number;
  passed: boolean | null;
  reason: string | null;
}

export interface GuardrailCheck {
  name: string;
  passed: boolean;
  score: number;
  reason: string | null;
  severity: string;
}

export interface EvalRun {
  id: string;
  name: string;
  model: string;
  timestamp: string;
  results: EvalResult[];
  avgScore: number;
  passRate: number;
}

export async function fetchEvalResults(): Promise<EvalRun[]> {
  const resp = await fetch("/api/evals");
  if (!resp.ok) return [];
  return resp.json();
}

export async function fetchGuardrailLogs(): Promise<GuardrailCheck[]> {
  const resp = await fetch("/api/guardrails");
  if (!resp.ok) return [];
  return resp.json();
}

export function loadLocalResults(): EvalRun[] {
  try {
    const raw = localStorage.getItem("aigis_results");
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveLocalResults(runs: EvalRun[]) {
  localStorage.setItem("aigis_results", JSON.stringify(runs));
}
