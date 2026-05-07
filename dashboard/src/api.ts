export interface EvalResult {
  name: string;
  score: number;
  passed: boolean | null;
  reason: string | null;
}

export interface EvalSummary {
  total: number;
  passed: number;
  failed: number;
  avg_score: number;
  pass_rate: number;
  latency_ms?: number;
}

export interface EvalRun {
  id: string;
  name: string;
  timestamp: string;
  results: EvalResult[];
  summary: EvalSummary;
}

export interface GuardrailCheck {
  id: string;
  name: string;
  passed: boolean;
  score: number;
  reason: string | null;
  severity: string;
  redacted?: string | null;
}

export interface GuardrailLog {
  id: string;
  timestamp: string;
  text: string;
  results: GuardrailCheck[];
  passed: boolean;
}

const API_BASE = "/api";

export async function fetchEvalResults(): Promise<EvalRun[]> {
  try {
    const resp = await fetch(`${API_BASE}/evals`);
    if (!resp.ok) return [];
    return resp.json();
  } catch {
    return loadLocalResults();
  }
}

export async function fetchGuardrailLogs(): Promise<GuardrailLog[]> {
  try {
    const resp = await fetch(`${API_BASE}/guardrails`);
    if (!resp.ok) return [];
    return resp.json();
  } catch {
    return [];
  }
}

export async function runEval(configYaml: string, name?: string): Promise<EvalRun> {
  const resp = await fetch(`${API_BASE}/evals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config_yaml: configYaml, name }),
  });
  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.detail || "Eval failed");
  }
  return resp.json();
}

export async function checkGuardrails(
  text: string,
  rails?: string[],
): Promise<GuardrailLog> {
  const resp = await fetch(`${API_BASE}/guardrails/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, rails }),
  });
  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.detail || "Guard check failed");
  }
  return resp.json();
}

export async function deleteEval(id: string): Promise<void> {
  await fetch(`${API_BASE}/evals/${id}`, { method: "DELETE" });
}

export async function deleteGuardrailLog(id: string): Promise<void> {
  await fetch(`${API_BASE}/guardrails/${id}`, { method: "DELETE" });
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
