import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { FileText, Shield, AlertTriangle, TrendingUp } from "lucide-react";
import type { EvalRun } from "../api";

interface OverviewProps {
  evalRuns: EvalRun[];
}

export function Overview({ evalRuns }: OverviewProps) {
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
    { label: "Active Rails", value: "2", icon: AlertTriangle, color: "from-amber-500 to-orange-600" },
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
