import type { Page } from "../App";
import {
  Shield,
  BarChart3,
  AlertTriangle,
  FileText,
  Grip,
  ScrollText,
  Settings,
  List,
} from "lucide-react";

const navItems: { page: Page; label: string; icon: typeof Shield }[] = [
  { page: "overview", label: "Overview", icon: BarChart3 },
  { page: "evals", label: "Evaluations", icon: FileText },
  { page: "guardrails", label: "Guardrails", icon: Shield },
  { page: "guardlogs", label: "Guard Logs", icon: List },
  { page: "reports", label: "Reports", icon: AlertTriangle },
  { page: "audit", label: "Audit", icon: ScrollText },
  { page: "settings", label: "Settings", icon: Settings },
];

interface SidebarProps {
  currentPage: Page;
  onNavigate: (page: Page) => void;
}

export function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  return (
    <aside className="w-64 bg-indigo-950/50 border-r border-indigo-900/50 flex flex-col">
      <div className="p-6 border-b border-indigo-900/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">AIGIS</h1>
            <p className="text-xs text-indigo-300">Guardrail & Integration</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ page, label, icon: Icon }) => (
          <button
            key={page}
            onClick={() => onNavigate(page)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
              currentPage === page
                ? "bg-indigo-600/20 text-indigo-200 border border-indigo-500/30 shadow-sm"
                : "text-indigo-300/70 hover:bg-indigo-800/20 hover:text-indigo-200 border border-transparent"
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </nav>
      <div className="p-4 border-t border-indigo-900/50">
        <div className="flex items-center gap-2 text-xs text-indigo-400">
          <Grip className="w-3 h-3" />
          v0.2.3
        </div>
      </div>
    </aside>
  );
}
