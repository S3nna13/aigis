import { useState } from "react";
import { FileText, Download, Trash2, RefreshCw } from "lucide-react";
import { sanitize } from "../api";

interface Report {
    id: string;
    name: string;
    timestamp: string;
    type: "eval" | "guardrail";
    summary?: {
        total: number;
        passed: number;
        failed: number;
        avg_score: number;
        pass_rate: number;
    };
}

const defaultReports: Report[] = [];

export default function Reports() {
    const [reports, setReports] = useState<Report[]>(defaultReports);
    const [loading, setLoading] = useState(false);

    const fetchReports = async () => {
        setLoading(true);
        try {
            const res = await fetch("/api/evals");
            const evals = await res.json();
            const mapped: Report[] = evals.map((e: any) => ({
                id: e.id,
                name: e.name,
                timestamp: e.timestamp,
                type: "eval" as const,
                summary: e.summary,
            }));
            setReports(mapped);
        } catch {
            const stored = localStorage.getItem("aigis_reports");
            if (stored) {
                setReports(JSON.parse(stored));
            }
        } finally {
            setLoading(false);
        }
    };

    const deleteReport = (id: string) => {
        const updated = reports.filter((r) => r.id !== id);
        setReports(updated);
        localStorage.setItem("aigis_reports", JSON.stringify(updated));
    };

    const formatDate = (ts: string) => {
        try {
            return new Date(ts).toLocaleString();
        } catch {
            return ts;
        }
    };

    return (
        <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
                <h2 style={{ fontSize: "1.5rem", fontWeight: 600 }}>Reports</h2>
                <button
                    onClick={fetchReports}
                    disabled={loading}
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        padding: "0.5rem 1rem",
                        background: "#3b82f6",
                        color: "white",
                        border: "none",
                        borderRadius: "0.5rem",
                        cursor: loading ? "wait" : "pointer",
                        fontSize: "0.875rem",
                    }}
                >
                    <RefreshCw size={16} />
                    {loading ? "Loading..." : "Refresh"}
                </button>
            </div>

            {reports.length === 0 ? (
                <div
                    style={{
                        textAlign: "center",
                        padding: "3rem",
                        background: "#1e293b",
                        borderRadius: "0.75rem",
                        color: "#94a3b8",
                    }}
                >
                    <FileText size={48} style={{ marginBottom: "1rem", opacity: 0.5 }} />
                    <p>No reports yet. Run evaluations to generate reports.</p>
                    <button
                        onClick={fetchReports}
                        style={{
                            marginTop: "1rem",
                            padding: "0.5rem 1.5rem",
                            background: "#3b82f6",
                            color: "white",
                            border: "none",
                            borderRadius: "0.5rem",
                            cursor: "pointer",
                        }}
                    >
                        Check for Reports
                    </button>
                </div>
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                    {reports.map((report) => (
                        <div
                            key={report.id}
                            style={{
                                background: "#1e293b",
                                borderRadius: "0.75rem",
                                padding: "1.25rem",
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                            }}
                        >
                            <div>
                                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.25rem" }}>
                                    <FileText size={18} style={{ color: "#3b82f6" }} />
                                    <span style={{ fontWeight: 600 }}>{sanitize(report.name)}</span>
                                    <span
                                        style={{
                                            fontSize: "0.75rem",
                                            padding: "0.125rem 0.5rem",
                                            borderRadius: "9999px",
                                            background: report.type === "eval" ? "#1e3a5f" : "#3b1e5f",
                                            color: report.type === "eval" ? "#60a5fa" : "#c084fc",
                                        }}
                                    >
                                        {report.type}
                                    </span>
                                </div>
                                <div style={{ fontSize: "0.875rem", color: "#94a3b8" }}>
                                    {formatDate(report.timestamp)}
                                    {report.summary && (
                                        <span style={{ marginLeft: "1rem" }}>
                                            {report.summary.passed}/{report.summary.total} passed | Avg:{" "}
                                            {report.summary.avg_score.toFixed(2)}
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div style={{ display: "flex", gap: "0.5rem" }}>
                                <button
                                    onClick={() => {
                                        const blob = new Blob([JSON.stringify(report, null, 2)], {
                                            type: "application/json",
                                        });
                                        const url = URL.createObjectURL(blob);
                                        const a = document.createElement("a");
                                        a.href = url;
                                        a.download = `report_${report.id}.json`;
                                        a.click();
                                    }}
                                    style={{
                                        padding: "0.375rem 0.75rem",
                                        background: "#334155",
                                        border: "none",
                                        borderRadius: "0.375rem",
                                        color: "#e2e8f0",
                                        cursor: "pointer",
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "0.375rem",
                                        fontSize: "0.8125rem",
                                    }}
                                >
                                    <Download size={14} /> Export
                                </button>
                                <button
                                    onClick={() => deleteReport(report.id)}
                                    style={{
                                        padding: "0.375rem 0.75rem",
                                        background: "#7f1d1d",
                                        border: "none",
                                        borderRadius: "0.375rem",
                                        color: "#fca5a5",
                                        cursor: "pointer",
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "0.375rem",
                                        fontSize: "0.8125rem",
                                    }}
                                >
                                    <Trash2 size={14} /> Delete
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
