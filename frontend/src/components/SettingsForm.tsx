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
    <div className="space-y-8 p-1 overflow-y-auto max-h-[600px] scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
      {/* Bot Parameters */}
      <div className="space-y-4">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest border-b border-zinc-800 pb-2">
          Engine Configuration
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-zinc-400">Bot Speed (1-10)</label>
            <input
              type="number"
              min="1"
              max="10"
              value={data.bot_speed || 5}
              onChange={(e) => handleChange("bot_speed", parseInt(e.target.value))}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-zinc-400">Logs Folder</label>
            <input
              type="text"
              value={data.logs_folder_path || "logs/"}
              onChange={(e) => handleChange("logs_folder_path", e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50"
            />
          </div>
        </div>
      </div>

      {/* Modes */}
      <div className="space-y-4">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest border-b border-zinc-800 pb-2">
          Operational Modes
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { key: "run_non_stop", label: "Run Non-Stop", desc: "Restart cycles automatically" },
            { key: "stealth_mode", label: "Stealth Mode", desc: "Human-like typing speed" },
            { key: "safe_mode", label: "Safe Mode", desc: "Extra randomized delays" },
            { key: "smooth_scroll", label: "Smooth Scroll", desc: "Visual scrolling in browser" },
            { key: "showAiErrorAlerts", label: "AI Error Alerts", desc: "Notify on LLM failures" },
            { key: "run_in_background", label: "Headless Mode", desc: "Hide browser window" }
          ].map((mode) => (
            <div key={mode.key} className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-blue-500/20 transition-all group">
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold text-zinc-300">{mode.label}</span>
                <label className="relative cursor-pointer">
                  <input
                    type="checkbox"
                    checked={data[mode.key] || false}
                    onChange={(e) => handleChange(mode.key, e.target.checked)}
                    className="sr-only"
                  />
                  <div className={`w-8 h-4 rounded-full transition-colors ${data[mode.key] ? 'bg-blue-600' : 'bg-zinc-800'}`}></div>
                  <div className={`absolute top-0.5 left-0.5 size-3 bg-white rounded-full transition-transform ${data[mode.key] ? 'translate-x-4' : 'translate-x-0'}`}></div>
                </label>
              </div>
              <p className="text-[10px] text-zinc-500 leading-tight">{mode.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
