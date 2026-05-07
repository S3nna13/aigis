import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { FileText, Shield, AlertTriangle, TrendingUp, Zap, Coins } from "lucide-react";
import { useEffect, useState } from "react";
import type { EvalRun } from "../api";

interface ApiMetrics {
  requests: number;
  latency_ms: { p50: number; p95: number; p99: number };
  tokens_used: number;
  estimated_cost_usd: number;
  window_minutes: number;
}

interface OverviewProps {
  evalRuns: EvalRun[];
}

export function Overview({ evalRuns }: OverviewProps) {
  const [metrics, setMetrics] = useState<ApiMetrics | null>(null);

  useEffect(() => {
    const url = new URL("/api/metrics", window.location.origin);
    if (!url.host.includes("localhost") && !url.host.includes("127.0.0.1")) {
      url.port = "8000";
    }
    fetch(url.toString())
      .then((r) => r.json())
      .then(setMetrics)
      .catch(() => null);
  }, []);

  const totalEvals = evalRuns.length;
  const avgScore = evalRuns.length
    ? evalRuns.reduce((s, r) => s + r.summary.avg_score, 0) / evalRuns.length
    : 0;
  const passRate = evalRuns.length
    ? evalRuns.reduce((s, r) => s + r.summary.pass_rate, 0) / evalRuns.length
    : 0;

  const chartData = [...evalRuns].reverse().slice(-10).map((r) => ({
    name: r.name.slice(0, 16),
    "Avg Score": +(r.summary.avg_score * 100).toFixed(0),
    "Pass Rate": +(r.summary.pass_rate * 100).toFixed(0),
  }));

  const stats = [
    { label: "Evaluations", value: totalEvals, icon: FileText, color: "from-blue-500 to-indigo-600" },
    { label: "Avg Score", value: `${(avgScore * 100).toFixed(0)}%`, icon: TrendingUp, color: "from-emerald-500 to-teal-600" },
    { label: "Pass Rate", value: `${(passRate * 100).toFixed(0)}%`, icon: Shield, color: "from-violet-500 to-purple-600" },
    { label: "Active Rails", value: "12", icon: AlertTriangle, color: "from-amber-500 to-orange-600" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-2">Dashboard Overview</h1>
      <p className="text-indigo-300/70 mb-8">Monitor your AI safety and evaluation metrics</p>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div
            key={label}
            className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl p-5 hover:border-indigo-700/50 transition-colors"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-indigo-300/70">{label}</span>
              <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center`}>
                <Icon className="w-4 h-4 text-white" />
              </div>
            </div>
            <p className="text-2xl font-bold text-white">{value}</p>
          </div>
        ))}
      </div>

      {metrics && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-indigo-300/70">API Requests</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <p className="text-2xl font-bold text-white">{metrics.requests}</p>
            <p className="text-xs text-indigo-400 mt-1">last {metrics.window_minutes}m</p>
          </div>
          <div className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-indigo-300/70">p95 Latency</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <p className="text-2xl font-bold text-white">{metrics.latency_ms.p95}ms</p>
            <p className="text-xs text-indigo-400 mt-1">p50: {metrics.latency_ms.p50}ms</p>
          </div>
          <div className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-indigo-300/70">Tokens Used</span>
              <Coins className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-2xl font-bold text-white">{(metrics.tokens_used / 1000).toFixed(1)}k</p>
            <p className="text-xs text-indigo-400 mt-1">${metrics.estimated_cost_usd.toFixed(4)} est.</p>
          </div>
          <div className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-indigo-300/70">p99 Latency</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <p className="text-2xl font-bold text-white">{metrics.latency_ms.p99}ms</p>
            <p className="text-xs text-indigo-400 mt-1">last {metrics.window_minutes}m</p>
          </div>
        </div>
      )}

      <div className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Recent Evaluations</h2>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <XAxis dataKey="name" stroke="#6366f1" tick={{ fontSize: 12 }} />
              <YAxis stroke="#6366f1" tick={{ fontSize: 12 }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  background: "#1e1b4b",
                  border: "1px solid #4338ca",
                  borderRadius: "8px",
                }}
              />
              <Bar dataKey="Avg Score" fill="#6366f1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Pass Rate" fill="#22c55e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-12 text-indigo-300/50">
            <p>No eval results yet.</p>
            <p className="text-sm mt-2">Run <code className="bg-indigo-900/50 px-2 py-1 rounded text-indigo-200">aigis eval examples/basic-eval.yaml</code> to get started</p>
          </div>
        )}
      </div>
    </div>
  );
}
