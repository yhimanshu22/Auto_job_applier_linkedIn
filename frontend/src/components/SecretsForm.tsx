"use client";

import React, { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { useSession } from "next-auth/react";

import { apiFetch, encodeUserId } from "@/lib/desktop-api";

/** Stored via LinkedIn API — excluded from secrets.py editor sync. */
export const LINKEDIN_SECRET_KEYS = new Set([
  "username",
  "password",
  "linkedin_extra_accounts",
]);

export type SecretsFormHandle = {
  /** Persist LinkedIn rows; returns false when validation fails. */
  saveLinkedInAccounts: () => Promise<boolean>;
  hasLinkedInEdits: () => boolean;
};

interface ApiLinkedInAccount {
  username: string;
  primary: boolean;
  has_password: boolean;
  deletable?: boolean;
}

interface AccountRow {
  id: string;
  username: string;
  password: string;
  passwordSet: boolean;
  saved: boolean;
  deletable: boolean;
}

function newRowId(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `row-${Date.now()}-${Math.random().toString(36).slice(2)}`;
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
    id: a.username ? `saved-${a.username}` : newRowId(),
    username: a.username || "",
    password: "",
    passwordSet: a.has_password,
    saved: true,
    deletable: a.deletable !== false,
  }));
}

function emptyPrimaryRow(): AccountRow {
  return {
    id: newRowId(),
    username: "",
    password: "",
    passwordSet: false,
    saved: false,
    deletable: true,
  };
}

function validateRows(rows: AccountRow[]): string | null {
  const filled = rows.filter((row) => row.username.trim() || row.password.trim());
  if (filled.length === 0) {
    return "Enter your LinkedIn email and password.";
  }
  for (const row of filled) {
    const email = row.username.trim();
    if (!email) {
      return "Each row needs a LinkedIn email.";
    }
    if (!row.password.trim() && !row.passwordSet) {
      return `Password required for ${email} (new account).`;
    }
  }
  return null;
}

/**
 * LinkedIn accounts (API) + AI/API keys from same secrets category as validator validate_secrets.
 */
const SecretsForm = forwardRef<SecretsFormHandle, SecretsFormProps>(function SecretsForm(
  { data, onChange, onAccountsSaved, onNotify, isActive = true },
  ref
) {
  const patch = (key: string, value: any) => onChange({ ...data, [key]: value });

  const { data: session } = useSession();
  const userId = session?.user?.email;

  const [accountRows, setAccountRows] = useState<AccountRow[]>([emptyPrimaryRow()]);
  const [accountCount, setAccountCount] = useState(0);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [msg, setMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const dirtyRef = useRef(false);

  const notify = (type: "success" | "error" | "warning", text: string) => {
    if (onNotify) {
      onNotify({ type, text });
      return;
    }
    setMsg({ type: type === "success" ? "ok" : "err", text });
  };

  const loadLinkedIn = async () => {
    if (!userId) {
      setLoading(false);
      setAccountRows([emptyPrimaryRow()]);
      setAccountCount(0);
      return;
    }
    if (dirtyRef.current) return;

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
            id: `saved-${String(d.primary_username)}`,
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
      setDirty(false);
      dirtyRef.current = false;
    } catch (e: unknown) {
      const err = e instanceof Error ? e.message : "Could not load LinkedIn accounts";
      notify("error", err);
      setAccountRows([emptyPrimaryRow()]);
      setAccountCount(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isActive || !userId) return;
    loadLinkedIn();
  }, [isActive, userId]);

  const patchRow = (i: number, field: "username" | "password", value: string) => {
    dirtyRef.current = true;
    setDirty(true);
    setAccountRows((rows) => {
      const next = [...rows];
      next[i] = { ...next[i], [field]: value };
      return next;
    });
  };

  const addAccount = () => {
    dirtyRef.current = true;
    setDirty(true);
    setAccountRows((rows) => [
      ...rows,
      {
        id: newRowId(),
        username: "",
        password: "",
        passwordSet: false,
        saved: false,
        deletable: true,
      },
    ]);
  };

  const deleteAccount = async (username: string) => {
    const u = username.trim();
    if (!u || !userId) return false;
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
      dirtyRef.current = false;
      setDirty(false);
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
    dirtyRef.current = true;
    setDirty(true);
    const next = accountRows.filter((_, j) => j !== i);
    setAccountRows(next.length > 0 ? next : [emptyPrimaryRow()]);
  };

  const saveLinkedIn = async (): Promise<boolean> => {
    setMsg(null);
    if (!userId) {
      notify("error", "Sign in to save LinkedIn accounts.");
      return false;
    }

    const validationError = validateRows(accountRows);
    if (validationError) {
      notify("error", validationError);
      return false;
    }

    setSaving(true);
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
      dirtyRef.current = false;
      setDirty(false);
      onAccountsSaved?.();
      await loadLinkedIn();
      return true;
    } catch (e: unknown) {
      notify("error", e instanceof Error ? e.message : "Save failed");
      return false;
    } finally {
      setSaving(false);
    }
  };

  useImperativeHandle(ref, () => ({
    saveLinkedInAccounts: saveLinkedIn,
    hasLinkedInEdits: () => dirtyRef.current,
  }));

  const aiProviders = ["openai", "deepseek", "gemini"];
  const savedRowCount = accountRows.filter((r) => r.saved && r.username.trim()).length;

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="flex-1 overflow-y-auto p-1 space-y-10 scrollbar-thin scrollbar-thumb-zinc-900">
        <div>
          <div className="flex items-center justify-between border-b border-zinc-900 pb-1.5 mb-3">
            <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">LinkedIn accounts</h3>
            {!loading && (
              <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-500">
                {accountCount} configured{dirty ? " · unsaved" : ""}
              </span>
            )}
          </div>

          <div className="rounded-lg border border-blue-500/25 bg-blue-500/5 px-3 py-2.5 mb-3">
            <p className="text-[10px] text-blue-100/90 leading-relaxed">
              Enter your LinkedIn email and password below, then click{" "}
              <span className="font-semibold text-white">Save LinkedIn accounts</span> (or the top{" "}
              <span className="font-semibold text-white">Save</span> button). Password is stored only on this
              computer. Leave password blank on an existing account to keep the saved value.
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

          {!userId ? (
            <p className="text-xs text-zinc-500">Loading session…</p>
          ) : loading ? (
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
                    key={row.id}
                    className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-3 items-end p-3 rounded-lg border border-zinc-900 bg-zinc-950/50"
                  >
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">
                        LinkedIn email
                      </label>
                      <input
                        type="email"
                        inputMode="email"
                        autoComplete="username"
                        value={row.username}
                        onChange={(e) => patchRow(i, "username", e.target.value)}
                        placeholder="you@email.com"
                        className="w-full bg-zinc-950 border border-zinc-900 rounded px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-blue-600"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-tight">
                        Password
                      </label>
                      <input
                        type="password"
                        autoComplete="current-password"
                        value={row.password}
                        onChange={(e) => patchRow(i, "password", e.target.value)}
                        placeholder={row.passwordSet ? "blank = keep saved" : "required"}
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
            </>
          )}
        </div>

        <div>
          <h3 className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest border-b border-zinc-900 pb-1.5 mb-3">
            AI & API (secrets.py)
          </h3>
          <p className="text-[9px] text-zinc-600 mb-4">
            API keys for the job bot. Use the top <span className="font-semibold text-zinc-400">Save</span> button
            to persist these with your LinkedIn accounts.
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

      {!loading && userId && (
        <div className="shrink-0 flex flex-wrap gap-2 pt-3 mt-2 border-t border-zinc-900 bg-zinc-950/80">
          <button
            type="button"
            onClick={saveLinkedIn}
            disabled={saving || !userId}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-[10px] font-bold uppercase tracking-widest hover:bg-blue-500 disabled:opacity-50"
          >
            {saving ? "Saving…" : dirty ? "Save LinkedIn accounts *" : "Save LinkedIn accounts"}
          </button>
          <button
            type="button"
            onClick={() => {
              dirtyRef.current = false;
              setDirty(false);
              loadLinkedIn();
            }}
            disabled={saving}
            className="px-4 py-2 rounded-lg border border-zinc-800 text-zinc-400 text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-900"
          >
            Reload
          </button>
        </div>
      )}
    </div>
  );
});

export default SecretsForm;
