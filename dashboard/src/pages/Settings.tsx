import { useState } from "react";
import { Settings, Key, Globe, Zap, Database, Info } from "lucide-react";

export function SettingsPage() {
  const [saved, setSaved] = useState(false);

  const [apiKey, setApiKey] = useState(() => localStorage.getItem("aigis_api_key") || "");
  const [corsOrigins, setCorsOrigins] = useState(
    () => localStorage.getItem("aigis_cors_origins") || "http://localhost:5173,http://127.0.0.1:5173"
  );
  const [rateLimit, setRateLimit] = useState(
    () => localStorage.getItem("aigis_rate_limit") || "100"
  );
  const [rateWindow, setRateWindow] = useState(
    () => localStorage.getItem("aigis_rate_window") || "60"
  );

  const handleSave = () => {
    localStorage.setItem("aigis_api_key", apiKey);
    localStorage.setItem("aigis_cors_origins", corsOrigins);
    localStorage.setItem("aigis_rate_limit", rateLimit);
    localStorage.setItem("aigis_rate_window", rateWindow);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleClear = () => {
    localStorage.removeItem("aigis_api_key");
    localStorage.removeItem("aigis_cors_origins");
    localStorage.removeItem("aigis_rate_limit");
    localStorage.removeItem("aigis_rate_window");
    setApiKey("");
    setCorsOrigins("http://localhost:5173,http://127.0.0.1:5173");
    setRateLimit("100");
    setRateWindow("60");
  };

  const sections = [
    {
      title: "Authentication",
      icon: Key,
      fields: [
        {
          label: "API Key",
          key: "AIGIS_API_KEY",
          type: "password",
          value: apiKey,
          onChange: setApiKey,
          placeholder: "Set your API key for production access",
          help: "Sent as X-API-Key header. Server requires this in production.",
        },
      ],
    },
    {
      title: "Network",
      icon: Globe,
      fields: [
        {
          label: "CORS Origins",
          key: "AIGIS_CORS_ORIGINS",
          type: "text",
          value: corsOrigins,
          onChange: setCorsOrigins,
          placeholder: "https://yourdomain.com,https://app.yourdomain.com",
          help: "Comma-separated list of allowed origins. Never use * in production.",
        },
      ],
    },
    {
      title: "Rate Limiting",
      icon: Zap,
      fields: [
        {
          label: "Requests per Window",
          key: "AIGIS_RATE_LIMIT",
          type: "number",
          value: rateLimit,
          onChange: setRateLimit,
          placeholder: "100",
          help: "Maximum requests per IP per window.",
        },
        {
          label: "Window Size (seconds)",
          key: "AIGIS_RATE_WINDOW",
          type: "number",
          value: rateWindow,
          onChange: setRateWindow,
          placeholder: "60",
          help: "Time window in seconds for rate limiting.",
        },
      ],
    },
    {
      title: "Data",
      icon: Database,
      fields: [
        {
          label: "Reports Directory",
          key: "AIGIS_DATA_DIR",
          type: "text",
          value: localStorage.getItem("aigis_data_dir") || "./reports",
          onChange: (v: string) => localStorage.setItem("aigis_data_dir", v),
          placeholder: "./reports",
          help: "Directory where eval and guardrail JSON reports are stored.",
        },
      ],
    },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-2">Settings</h1>
      <p className="text-indigo-300/70 mb-8">Configure AIGIS server and client behaviour</p>

      <div className="max-w-2xl space-y-6">
        {sections.map(({ title, icon: Icon, fields }) => (
          <div
            key={title}
            className="bg-indigo-950/40 border border-indigo-900/50 rounded-xl overflow-hidden"
          >
            <div className="flex items-center gap-3 px-6 py-4 border-b border-indigo-900/50">
              <Icon className="w-4 h-4 text-indigo-400" />
              <h2 className="text-sm font-semibold text-indigo-200">{title}</h2>
            </div>
            <div className="px-6 py-5 space-y-5">
              {fields.map(({ label, key, type, value, onChange, placeholder, help }) => (
                <div key={key}>
                  <label className="block text-xs text-indigo-300/70 mb-1.5">
                    <span className="font-mono text-indigo-400/60">{key}</span>
                    {" — "}{label}
                  </label>
                  <input
                    type={type}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder}
                    className="w-full bg-indigo-950/80 border border-indigo-800/50 rounded-lg px-3 py-2 text-sm text-white placeholder-indigo-400/40 focus:outline-none focus:border-indigo-500/50"
                  />
                  {help && <p className="text-xs text-indigo-400/50 mt-1">{help}</p>}
                </div>
              ))}
            </div>
          </div>
        ))}

        <div className="bg-indigo-950/20 border border-indigo-900/40 rounded-xl p-5">
          <div className="flex items-start gap-3">
            <Info className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-indigo-300/60 space-y-1">
              <p>Settings are stored in browser localStorage and sent to the API server as environment variables.</p>
              <p>Changes take effect on the next server restart.</p>
              <p className="font-mono text-indigo-400/50 mt-2">
                AIGIS_API_KEY • AIGIS_CORS_ORIGINS • AIGIS_RATE_LIMIT • AIGIS_RATE_WINDOW • AIGIS_DATA_DIR
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {saved ? "Saved!" : "Save Settings"}
          </button>
          <button
            onClick={handleClear}
            className="px-5 py-2.5 bg-indigo-950/60 hover:bg-indigo-900/40 text-indigo-300 text-sm rounded-lg border border-indigo-800/40 transition-colors"
          >
            Reset to Defaults
          </button>
        </div>
      </div>
    </div>
  );
}