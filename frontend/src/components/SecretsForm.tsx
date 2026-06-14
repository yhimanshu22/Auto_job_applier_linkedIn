"use client";

import React, { useEffect, useState } from "react";
import { useSession } from "next-auth/react";

import { apiFetch, encodeUserId } from "@/lib/desktop-api";

interface ApiLinkedInAccount {
  username: string;
  primary: boolean;
  has_password: boolean;
  deletable?: boolean;
}

interface AccountRow {
  username: string;
  password: string;
  passwordSet: boolean;
  saved: boolean;
  deletable: boolean;
}

interface SecretsFormProps {
  data: Record<string, any>;
  onChange: (newData: Record<string, any>) => void;
  onAccountsSaved?: () => void;
  onNotify?: (message: { type: "success" | "error" | "warning"; text: string }) => void;
  /** When true (secrets tab visible), reload LinkedIn snapshot from API */
  isActive?: boolean;
}

function apiAccountsToRows(accounts: ApiLinkedInAccount[]): AccountRow[] {
  if (accounts.length === 0) return [];

  const primary = accounts.find((a) => a.primary);
  const ordered = primary
    ? [primary, ...accounts.filter((a) => a.username !== primary.username)]
    : accounts;

  return ordered.map((a) => ({
    username: a.username || "",
    password: "",
    passwordSet: a.has_password,
    saved: true,
    deletable: a.deletable !== false,
  }));
}

function emptyPrimaryRow(): AccountRow {
  return {
    username: "",
    password: "",
    passwordSet: false,
    saved: false,
    deletable: true,
  };
}

/**
 * LinkedIn accounts (API) + AI/API keys from same secrets category as validator validate_secrets.
 */
export default function SecretsForm({
  data,
  onChange,
  onAccountsSaved,
  onNotify,
  isActive = true,
}: SecretsFormProps) {
  const patch = (key: string, value: any) => onChange({ ...data, [key]: value });

  const { data: session } = useSession();
  const userId = session?.user?.email;

  const [accountRows, setAccountRows] = useState<AccountRow[]>([emptyPrimaryRow()]);
  const [accountCount, setAccountCount] = useState(0);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const notify = (type: "success" | "error", text: string) => {
    if (onNotify) {
      onNotify({ type, text });
      return;
    }
    setMsg({ type: type === "success" ? "ok" : "err", text });
  };

  const loadLinkedIn = async () => {
    setLoading(true);
    try {
      const r = await apiFetch(`/api/linkedin-accounts?user_id=${encodeUserId(userId)}`);
      if (!r.ok) throw new Error("Failed to load accounts");
      const d = await r.json();
      const accounts: ApiLinkedInAccount[] = Array.isArray(d.accounts) ? d.accounts : [];

      let rows = apiAccountsToRows(accounts);
      if (rows.length === 0 && d.primary_username) {
        rows = [
          {
            username: String(d.primary_username),
            password: "",
            passwordSet: !!d.primary_password_set,
            saved: true,
            deletable: true,
          },
        ];
      }
      if (rows.length === 0) {
        rows = [emptyPrimaryRow()];
      }

      setAccountRows(rows);
      const visibleCount = rows.filter((row) => row.username.trim()).length;
      setAccountCount(visibleCount);
    } catch {
      setAccountRows(
        data.username
          ? [
              {
                username: String(data.username),
                password: "",
                passwordSet: false,
                saved: false,
                deletable: true,
              },
            ]
          : [emptyPrimaryRow()]
      );
      setAccountCount(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isActive) return;
    loadLinkedIn();
  }, [isActive]);

  const patchRow = (i: number, field: "username" | "password", value: string) => {
    setAccountRows((rows) => {
      const next = [...rows];
      next[i] = { ...next[i], [field]: value };
      return next;
    });
  };

  const addAccount = () => {
    setAccountRows((rows) => [
      ...rows,
      { username: "", password: "", passwordSet: false, saved: false, deletable: true },
    ]);
  };

  const deleteAccount = async (username: string) => {
    const u = username.trim();
    if (!u) return false;
    setDeleting(u);
    setMsg(null);
    try {
      const r = await apiFetch(
        `/api/linkedin-accounts?username=${encodeURIComponent(u)}&user_id=${encodeUserId(userId)}`,
        { method: "DELETE" }
      );
      const raw = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof raw.detail === "string" ? raw.detail : r.statusText);
      notify("success", `Deleted ${u} (${raw.account_count ?? "?"} account(s) left).`);
      onAccountsSaved?.();
      await loadLinkedIn();
      return true;
    } catch (e: unknown) {
      notify("error", e instanceof Error ? e.message : "Delete failed");
      return false;
    } finally {
      setDeleting(null);
    }
  };

  const removeRow = async (i: number) => {
    const row = accountRows[i];
    if (row?.saved && row.username.trim()) {
      if (!(await deleteAccount(row.username))) return;
      return;
    }
    const next = accountRows.filter((_, j) => j !== i);
    setAccountRows(next.length > 0 ? next : [emptyPrimaryRow()]);
  };

  const saveLinkedIn = async () => {
    setSaving(true);
    setMsg(null);
    try {
      const filled = accountRows.filter((row) => row.username.trim());
      const primary = filled[0];
      const extras = filled.slice(1);

      const r = await apiFetch(`/api/linkedin-accounts?user_id=${encodeUserId(userId)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          primary_username: primary?.username.trim() || "",
          primary_password: primary?.password || "",
          extras: extras.map(({ username, password }) => ({ username, password })),
        }),
      });
      const raw = await r.json().catch(() => ({}));
      if (!r.ok) {
        const det = raw.detail;
        const text =
          typeof det === "string"
            ? det
            : Array.isArray(det)
              ? det.map((x: { msg?: string }) => x.msg || JSON.stringify(x)).join("; ")
              : r.statusText;
        throw new Error(text);
      }
      notify("success", `LinkedIn saved (${raw.account_count ?? "?"} account(s)).`);
      onAccountsSaved?.();
      await loadLinkedIn();
    } catch (e: unknown) {
      notify("error", e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const aiProviders = ["openai", "deepseek", "gemini"];
  const savedRowCount = accountRows.filter((r) => r.saved && r.username.trim()).length;

  return (
    <div className="space-y-10 p-1 overflow-y-auto max-h-[550px] scrollbar-thin scrollbar-thumb-zinc-900">
      <div>
        <div className="flex items-center justify-between border-b border-zinc-900 pb-1.5 mb-3">
          <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">LinkedIn accounts</h3>
          {!loading && (
            <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">
              {accountCount} configured
            </span>
          )}
        </div>

        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2 mb-3">
          <p className="text-[10px] text-amber-200/90 leading-relaxed">
            Save LinkedIn email and password here before starting the bot. Leave password blank to keep
            the saved value for that email. On first run the bot logs in in your browser (disable
            headless in Settings if you need to complete 2FA).
          </p>
        </div>

        {msg && !onNotify && (
          <div
            className={`text-[11px] px-3 py-2 rounded-lg border mb-3 ${
              msg.type === "ok"
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                : "border-red-500/30 bg-red-500/10 text-red-300"
            }`}
          >
            {msg.text}
          </div>
        )}

        {loading ? (
          <p className="text-xs text-zinc-500">Loading LinkedIn accounts…</p>
        ) : (
          <>
            <div className="flex justify-between items-center border-b border-zinc-900 pb-1.5 mb-3">
              <p className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">
                {savedRowCount > 0 ? `${savedRowCount} saved` : "Add your accounts"}
              </p>
              <button
                type="button"
                onClick={addAccount}
                className="text-[9px] font-bold text-blue-500 uppercase tracking-widest hover:text-blue-400"
              >
                + Add account
              </button>
            </div>

            <div className="space-y-3 mb-4">
              {accountRows.map((row, i) => (
                <div
                  key={`${row.username}-${i}`}
                  className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-3 items-end p-3 rounded-lg border border-zinc-900 bg-zinc-950/50"
                >
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Email</label>
                    <input
                      type="text"
                      autoComplete="username"
                      value={row.username}
                      onChange={(e) => patchRow(i, "username", e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-blue-600"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">Password</label>
                    <input
                      type="password"
                      autoComplete="current-password"
                      value={row.password}
                      onChange={(e) => patchRow(i, "password", e.target.value)}
                      placeholder={row.passwordSet ? "blank = keep saved" : "required for new account"}
                      className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-blue-600"
                    />
                  </div>
                  {row.deletable ? (
                    <button
                      type="button"
                      onClick={() => removeRow(i)}
                      disabled={deleting !== null || saving}
                      className="text-[10px] font-bold text-red-500/80 hover:text-red-400 uppercase py-2 disabled:opacity-50"
                    >
                      {deleting === row.username.trim() ? "Deleting…" : row.saved ? "Delete" : "Remove"}
                    </button>
                  ) : (
                    <span className="text-[10px] text-zinc-600 uppercase py-2">—</span>
                  )}
                </div>
              ))}
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={saveLinkedIn}
                disabled={saving}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-[10px] font-bold uppercase tracking-widest hover:bg-blue-500 disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save LinkedIn accounts"}
              </button>
              <button
                type="button"
                onClick={loadLinkedIn}
                disabled={saving}
                className="px-4 py-2 rounded-lg border border-zinc-800 text-zinc-400 text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-900"
              >
                Reload
              </button>
            </div>
          </>
        )}
      </div>

      <div>
        <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5 mb-3">
          AI & API (secrets.py)
        </h3>
        <p className="text-[9px] text-zinc-600 mb-4">
          Same keys as <span className="font-mono text-zinc-500">config/secrets</span> in the backend. Use the main{" "}
          <span className="font-semibold text-zinc-400">Save</span> button above the editor to persist with other
          tabs; or edit raw keys in Code mode.
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
  );
}
