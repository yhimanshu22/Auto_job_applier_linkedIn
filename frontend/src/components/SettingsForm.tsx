import React from 'react';

interface SettingsFormProps {
  data: Record<string, any>;
  onChange: (newData: Record<string, any>) => void;
}

export default function SettingsForm({ data, onChange }: SettingsFormProps) {
  const handleChange = (key: string, value: any) => {
    onChange({ ...data, [key]: value });
  };

  return (
    <div className="space-y-6 p-1 overflow-y-auto max-h-[550px] scrollbar-thin scrollbar-thumb-zinc-900">
      {/* Bot Parameters */}
      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Engine Configuration
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Bot Speed (1-10)</label>
            <input
              type="number"
              min="1"
              max="10"
              value={data.bot_speed || 5}
              onChange={(e) => handleChange("bot_speed", parseInt(e.target.value))}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Logs Folder</label>
            <input
              type="text"
              value={data.logs_folder_path || "logs/"}
              onChange={(e) => handleChange("logs_folder_path", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
        </div>
      </div>

      {/* Modes */}
      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Operational Modes
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { key: "run_non_stop", label: "Run Non-Stop", desc: "Restart cycles" },
            { key: "stealth_mode", label: "Stealth", desc: "Human patterns" },
            { key: "safe_mode", label: "Safe Mode", desc: "Extra delays" },
            { key: "smooth_scroll", label: "Scrolling", desc: "Visual scroll" },
            { key: "showAiErrorAlerts", label: "AI Alerts", desc: "LLM failures" },
            { key: "run_in_background", label: "Headless", desc: "Hide window" }
          ].map((mode) => (
            <div key={mode.key} className="p-3 bg-zinc-950/50 border border-zinc-900 rounded-lg hover:border-zinc-800 transition-all group">
              <div className="flex justify-between items-center mb-1">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-tight">{mode.label}</span>
                <label className="relative cursor-pointer">
                  <input
                    type="checkbox"
                    checked={data[mode.key] || false}
                    onChange={(e) => handleChange(mode.key, e.target.checked)}
                    className="sr-only"
                  />
                  <div className={`w-6 h-3 rounded-full transition-colors ${data[mode.key] ? 'bg-blue-600' : 'bg-zinc-900'}`}></div>
                  <div className={`absolute top-0.5 left-0.5 size-2 bg-white rounded-full transition-transform ${data[mode.key] ? 'translate-x-3' : 'translate-x-0'}`}></div>
                </label>
              </div>
              <p className="text-[9px] text-zinc-600 leading-tight">{mode.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
