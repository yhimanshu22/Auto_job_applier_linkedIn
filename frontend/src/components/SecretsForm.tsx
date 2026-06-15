"use client";

import React from "react";

interface SecretsFormProps {
  data: Record<string, any>;
  onChange: (newData: Record<string, any>) => void;
}

/**
 * AI/API keys from secrets.py. LinkedIn credentials are edited in Code view
 * (LINKEDIN_USERNAME, LINKEDIN_PASSWORD, LINKEDIN_USERNAME_1, …).
 */
export default function SecretsForm({ data, onChange }: SecretsFormProps) {
  const patch = (key: string, value: any) => onChange({ ...data, [key]: value });

  const aiProviders = ["openai", "deepseek", "gemini"];

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex-1 overflow-y-auto p-1 space-y-10 scrollbar-thin scrollbar-thumb-zinc-900">
        <div className="rounded-lg border border-blue-500/25 bg-blue-500/5 px-3 py-2.5">
          <p className="text-[10px] text-blue-100/90 leading-relaxed">
            LinkedIn emails and passwords are stored as{" "}
            <span className="font-mono text-white">LINKEDIN_USERNAME</span> /{" "}
            <span className="font-mono text-white">LINKEDIN_PASSWORD</span> (and{" "}
            <span className="font-mono text-white">_1</span>,{" "}
            <span className="font-mono text-white">_2</span>, … for extra accounts). Switch to{" "}
            <span className="font-semibold text-white">Code</span> view on this tab to edit them,
            then click <span className="font-semibold text-white">Save</span>.
          </p>
        </div>

        <div>
          <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5 mb-3">
            AI & API (secrets.py)
          </h3>
          <p className="text-[9px] text-zinc-600 mb-4">
            API keys for the job bot. Use the top <span className="font-semibold text-zinc-400">Save</span>{" "}
            button to persist.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 max-w-4xl">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={!!data.use_AI}
                onChange={(e) => patch("use_AI", e.target.checked)}
                className="rounded border-zinc-700 bg-zinc-950"
              />
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Use AI</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={!!data.stream_output}
                onChange={(e) => patch("stream_output", e.target.checked)}
                className="rounded border-zinc-700 bg-zinc-950"
              />
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Stream LLM output</span>
            </label>
            <div className="space-y-1 md:col-span-2">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">AI provider</label>
              <select
                value={data.ai_provider ?? "openai"}
                onChange={(e) => patch("ai_provider", e.target.value)}
                className="w-full max-w-md bg-zinc-950 border border-zinc-900 rounded px-3 py-2 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
              >
                {aiProviders.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1 md:col-span-2">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">LLM API base URL</label>
              <input
                type="text"
                value={data.llm_api_url ?? ""}
                onChange={(e) => patch("llm_api_url", e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-2 text-xs text-zinc-300 font-mono focus:outline-none focus:border-blue-600"
                placeholder="https://api.openai.com/v1"
              />
            </div>
            <div className="space-y-1 md:col-span-2">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">LLM API key</label>
              <input
                type="password"
                value={data.llm_api_key ?? ""}
                onChange={(e) => patch("llm_api_key", e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-2 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
                placeholder="••••••••"
              />
            </div>
            <div className="space-y-1 md:col-span-2">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Model name</label>
              <input
                type="text"
                value={data.llm_model ?? ""}
                onChange={(e) => patch("llm_model", e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-2 text-xs text-zinc-300 focus:outline-none focus:border-blue-600"
                placeholder="gpt-4o-mini, deepseek-chat, …"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
