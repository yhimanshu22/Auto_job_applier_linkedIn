import React from "react";

interface SettingsFormProps {
  data: Record<string, any>;
  onChange: (newData: Record<string, any>) => void;
}

/** Mirrors backend/modules/validator.py validate_settings + common DB keys (daily_apply_limit, showAiErrorAlerts). */
export default function SettingsForm({ data, onChange }: SettingsFormProps) {
  const patch = (key: string, value: any) => onChange({ ...data, [key]: value });

  const Toggle = ({ k, label, desc }: { k: string; label: string; desc?: string }) => (
    <div className="p-3 bg-zinc-950/50 border border-zinc-900 rounded-lg hover:border-zinc-800 transition-all group">
      <div className="flex justify-between items-center mb-1">
        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-tight">{label}</span>
        <label className="relative cursor-pointer">
          <input
            type="checkbox"
            checked={!!data[k]}
            onChange={(e) => patch(k, e.target.checked)}
            className="sr-only"
          />
          <div className={`w-6 h-3 rounded-full transition-colors ${data[k] ? "bg-blue-600" : "bg-zinc-900"}`} />
          <div
            className={`absolute top-0.5 left-0.5 size-2 bg-white rounded-full transition-transform ${
              data[k] ? "translate-x-3" : "translate-x-0"
            }`}
          />
        </label>
      </div>
      {desc && <p className="text-[9px] text-zinc-600 leading-tight">{desc}</p>}
    </div>
  );

  return (
    <div className="space-y-8 p-1 overflow-y-auto max-h-[550px] scrollbar-thin scrollbar-thumb-zinc-900">
      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Paths & limits
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
          <div className="space-y-1 md:col-span-2">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Applied jobs CSV path</label>
            <input
              type="text"
              value={data.file_name ?? ""}
              onChange={(e) => patch("file_name", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1 md:col-span-2">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Failed jobs CSV path</label>
            <input
              type="text"
              value={data.failed_file_name ?? ""}
              onChange={(e) => patch("failed_file_name", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Logs folder</label>
            <input
              type="text"
              value={data.logs_folder_path ?? "logs/"}
              onChange={(e) => patch("logs_folder_path", e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Daily Easy Apply limit</label>
            <input
              type="number"
              min={1}
              value={data.daily_apply_limit ?? 50}
              onChange={(e) => patch("daily_apply_limit", parseInt(e.target.value, 10) || 1)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Bot speed (1–10)</label>
            <input
              type="number"
              min={1}
              max={10}
              value={data.bot_speed ?? 5}
              onChange={(e) => patch("bot_speed", parseInt(e.target.value, 10) || 1)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Click gap (ms)</label>
            <input
              type="number"
              min={0}
              value={data.click_gap ?? 0}
              onChange={(e) => patch("click_gap", parseInt(e.target.value, 10) || 0)}
              className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
            />
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Run behavior
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <Toggle k="run_non_stop" label="Run non-stop" desc="Restart search cycles" />
          <Toggle k="alternate_sortby" label="Alternate sort by" desc="Toggle relevance / recent" />
          <Toggle k="cycle_date_posted" label="Cycle date posted" desc="Rotate date filters" />
          <Toggle k="stop_date_cycle_at_24hr" label="Stop date cycle at 24h" desc="When cycling date posted" />
          <Toggle k="close_tabs" label="Close extra tabs" />
          <Toggle k="follow_companies" label="Follow companies" desc="After apply when offered" />
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5">
          Browser / automation
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <Toggle k="run_in_background" label="Headless" desc="Background browser" />
          <Toggle k="disable_extensions" label="Disable extensions" />
          <Toggle k="safe_mode" label="Safe mode" desc="Guest-style profile delays" />
          <Toggle k="smooth_scroll" label="Smooth scroll" />
          <Toggle k="keep_screen_awake" label="Keep screen awake" />
          <Toggle k="stealth_mode" label="Stealth (UC)" desc="Undetected ChromeDriver" />
          <Toggle k="showAiErrorAlerts" label="AI error popups" desc="Pause on LLM errors" />
        </div>
      </div>
    </div>
  );
}
