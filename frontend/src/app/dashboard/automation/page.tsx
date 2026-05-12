"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";

const API = "http://127.0.0.1:8000/api/linkedin-automation";
const BILLING_API = "http://127.0.0.1:8000/api/billing";
const TABS = ["post", "engage", "pursue", "calendar", "settings"] as const;
type Tab = (typeof TABS)[number];

type Subscription = {
  plan?: string;
  status?: string;
};

function PlanPill({ plan }: { plan: string | undefined }) {
  const tone =
    plan === "pro"
      ? "text-indigo-400"
      : plan === "agency"
        ? "text-amber-400"
        : "text-zinc-500";
  return (
    <div className="px-2 py-0.5 rounded border border-zinc-800 bg-zinc-900">
      <span className={`text-[9px] font-bold uppercase tracking-wider ${tone}`}>
        {plan || "free"}
      </span>
    </div>
  );
}

type Stats = {
  total_all_time: number;
  last_24h: number;
  last_30d: number;
  running: number;
  by_action_30d: Record<string, number>;
  by_status_30d: Record<string, number>;
  plan: string;
  daily_limit: number;
  daily_used: number;
};

type FrameworkSettings = {
  openai_api_key?: string;
  openai_model?: string | null;
  gemini_api_key?: string;
  use_gemini?: boolean | null;
  headless?: boolean | null;
  marketing_mode?: boolean | null;
  project_name?: string | null;
  project_url?: string | null;
  project_pitch?: string | null;
  project_short_pitch?: string | null;
  project_context?: string | null;
  project_tagline?: string | null;
};

type Task = {
  id: string;
  action: string;
  status: string;
  exit_code: number | null;
  started_at: string | null;
  ended_at: string | null;
  running: boolean;
  args?: string[];
  log?: string;
  user_id?: string;
  account_username?: string | null;
};

type LinkedInAccount = {
  username: string;
  primary: boolean;
  has_password: boolean;
};

type AccountsPayload = {
  accounts: LinkedInAccount[];
  active: string | null;
};

// Persistent dashboard form defaults — mirrors backend ``ALLOWED_FORM_KEYS``.
// Every key is optional because the DB stores partial state and ``null`` is
// used to clear an individual key on the next save.
type FormDefaults = {
  tab?: Tab;
  selected_account?: string;
  // common flags
  common_debug?: boolean;
  common_headless?: boolean | null;
  common_no_ai?: boolean;
  // post
  post_text?: string;
  post_images_dir?: string;
  post_no_images?: boolean;
  post_topics_file?: string;
  post_schedule_date?: string;
  post_schedule_time?: string;
  // engage
  engage_action?: "like" | "comment" | "both";
  engage_max_actions?: number;
  // pursue
  pursue_profile_name?: string;
  pursue_max_posts?: number;
  pursue_perspectives?: string;
  pursue_bio_keywords?: string;
  pursue_do_follow?: boolean;
  pursue_do_like?: boolean;
  pursue_do_comment?: boolean;
  // calendar
  calendar_niche?: string;
  calendar_total_posts?: number;
  calendar_output?: string;
};

type Message = { type: "success" | "error" | "warning"; text: string };

async function parseErr(res: Response): Promise<string> {
  try {
    const j = await res.json();
    if (typeof j?.detail === "string") return j.detail;
    if (Array.isArray(j?.detail))
      return (
        j.detail
          .map((x: { msg?: string }) => x?.msg || "")
          .filter(Boolean)
          .join("; ") || res.statusText
      );
    return res.statusText || "Request failed";
  } catch {
    return res.statusText || "Request failed";
  }
}

function fmtTime(iso: string | null | undefined) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function StatusPill({ task }: { task: Task }) {
  const tone = task.running
    ? "bg-blue-600/15 text-blue-400 border-blue-500/20"
    : task.status === "completed"
      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
      : task.status === "stopped"
        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
        : "bg-red-500/10 text-red-400 border-red-500/20";
  const label = task.running ? "running" : task.status;
  return (
    <span
      className={`inline-flex px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-tight border ${tone}`}
    >
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Action forms
// ---------------------------------------------------------------------------

type CommonState = { debug: boolean; headless: boolean | null; no_ai: boolean };
const COMMON_DEFAULT: CommonState = { debug: false, headless: null, no_ai: false };

function CommonOptions({
  v,
  onChange,
}: {
  v: CommonState;
  onChange: (s: CommonState) => void;
}) {
  const Toggle = ({
    label,
    val,
    onSet,
  }: {
    label: string;
    val: boolean;
    onSet: (b: boolean) => void;
  }) => (
    <label className="flex items-center gap-2 text-[10px] font-bold text-zinc-500 uppercase tracking-widest cursor-pointer">
      <input
        type="checkbox"
        checked={val}
        onChange={(e) => onSet(e.target.checked)}
        className="size-3.5 rounded accent-blue-600"
      />
      {label}
    </label>
  );
  return (
    <div className="grid grid-cols-3 gap-3 p-3 rounded-lg bg-zinc-900/40 border border-zinc-900">
      <Toggle label="Debug" val={v.debug} onSet={(b) => onChange({ ...v, debug: b })} />
      <Toggle
        label="Force Headless"
        val={!!v.headless}
        onSet={(b) => onChange({ ...v, headless: b ? true : null })}
      />
      <Toggle label="No AI" val={v.no_ai} onSet={(b) => onChange({ ...v, no_ai: b })} />
    </div>
  );
}

function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <label className="block space-y-1">
      <span className="block text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
        {label}
      </span>
      {children}
      {hint && <span className="block text-[10px] text-zinc-600">{hint}</span>}
    </label>
  );
}

const inputCls =
  "w-full px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-200 text-xs focus:outline-none focus:border-blue-600 transition-colors";

// Shared shape for the per-form props that mirror state into the DB. Each
// form reads its initial values from ``defaults``, writes back through
// ``patchDefaults`` whenever its inputs change, and exposes a "Clear" button
// wired to ``onClearDefaults``.
type FormPersistenceProps = {
  common: CommonState;
  setCommon: (s: CommonState) => void;
  onSubmit: (body: Record<string, unknown>) => Promise<void>;
  busy: boolean;
  defaults: FormDefaults;
  patchDefaults: (patch: Partial<FormDefaults>) => void;
  onClearDefaults: () => void;
};

function PostForm({
  common,
  setCommon,
  onSubmit,
  busy,
  defaults,
  patchDefaults,
  onClearDefaults,
}: FormPersistenceProps) {
  const [postText, setPostText] = useState(defaults.post_text ?? "");
  const [imagesDir, setImagesDir] = useState(defaults.post_images_dir ?? "");
  const [noImages, setNoImages] = useState(defaults.post_no_images ?? false);
  const [topicsFile, setTopicsFile] = useState(defaults.post_topics_file ?? "");
  const [scheduleDate, setScheduleDate] = useState(
    defaults.post_schedule_date ?? ""
  );
  const [scheduleTime, setScheduleTime] = useState(
    defaults.post_schedule_time ?? ""
  );

  // Mirror local state into the persisted defaults so the next page load
  // re-hydrates whatever the user typed. ``patchDefaults`` is memoised and
  // de-duplicates same-value writes, so this effect is cheap.
  useEffect(() => {
    patchDefaults({
      post_text: postText,
      post_images_dir: imagesDir,
      post_no_images: noImages,
      post_topics_file: topicsFile,
      post_schedule_date: scheduleDate,
      post_schedule_time: scheduleTime,
    });
  }, [postText, imagesDir, noImages, topicsFile, scheduleDate, scheduleTime, patchDefaults]);

  return (
    <div className="space-y-4">
      <Field label="Post text" hint="Leave empty to draw a topic from the topics file.">
        <textarea
          value={postText}
          onChange={(e) => setPostText(e.target.value)}
          rows={4}
          placeholder="Hello LinkedIn 👋"
          className={`${inputCls} resize-none`}
        />
      </Field>
      <div className="grid sm:grid-cols-2 gap-3">
        <Field label="Images dir" hint="Optional absolute path">
          <input
            value={imagesDir}
            onChange={(e) => setImagesDir(e.target.value)}
            placeholder="./static"
            className={inputCls}
          />
        </Field>
        <Field label="Topics file" hint="Optional, defaults to topics.txt">
          <input
            value={topicsFile}
            onChange={(e) => setTopicsFile(e.target.value)}
            placeholder="topics.txt"
            className={inputCls}
          />
        </Field>
        <Field label="Schedule date" hint="mm/dd/yyyy">
          <input
            value={scheduleDate}
            onChange={(e) => setScheduleDate(e.target.value)}
            placeholder="09/16/2025"
            className={inputCls}
          />
        </Field>
        <Field label="Schedule time" hint='e.g. "10:45 AM"'>
          <input
            value={scheduleTime}
            onChange={(e) => setScheduleTime(e.target.value)}
            placeholder="10:45 AM"
            className={inputCls}
          />
        </Field>
      </div>
      <label className="flex items-center gap-2 text-[10px] font-bold text-zinc-500 uppercase tracking-widest cursor-pointer">
        <input
          type="checkbox"
          checked={noImages}
          onChange={(e) => setNoImages(e.target.checked)}
          className="size-3.5 rounded accent-blue-600"
        />
        Disable image uploads
      </label>
      <CommonOptions v={common} onChange={setCommon} />
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          disabled={busy}
          onClick={() =>
            onSubmit({
              post_text: postText || undefined,
              images_dir: imagesDir || undefined,
              topics_file: topicsFile || undefined,
              no_images: noImages || undefined,
              schedule_date: scheduleDate || undefined,
              schedule_time: scheduleTime || undefined,
              ...common,
            })
          }
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold uppercase tracking-widest transition-all disabled:opacity-50"
        >
          {busy ? "Launching…" : "Create post"}
        </button>
        <ClearDefaultsButton onClear={onClearDefaults} />
      </div>
    </div>
  );
}

function ClearDefaultsButton({ onClear }: { onClear: () => void }) {
  return (
    <button
      type="button"
      onClick={onClear}
      className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest hover:text-red-400 transition-colors"
      title="Forget the saved defaults for this form (server-side)"
    >
      Clear saved defaults
    </button>
  );
}

function EngageForm({
  common,
  setCommon,
  onSubmit,
  busy,
  defaults,
  patchDefaults,
  onClearDefaults,
}: FormPersistenceProps) {
  const [engageAction, setEngageAction] = useState<"like" | "comment" | "both">(
    defaults.engage_action ?? "both"
  );
  const [maxActions, setMaxActions] = useState(defaults.engage_max_actions ?? 5);

  useEffect(() => {
    patchDefaults({
      engage_action: engageAction,
      engage_max_actions: maxActions,
    });
  }, [engageAction, maxActions, patchDefaults]);

  return (
    <div className="space-y-4">
      <div className="grid sm:grid-cols-2 gap-3">
        <Field label="Engagement type">
          <select
            value={engageAction}
            onChange={(e) =>
              setEngageAction(e.target.value as "like" | "comment" | "both")
            }
            className={inputCls}
          >
            <option value="both">Like + Comment</option>
            <option value="like">Like only</option>
            <option value="comment">Comment only</option>
          </select>
        </Field>
        <Field label="Max actions">
          <input
            type="number"
            min={1}
            max={50}
            value={maxActions}
            onChange={(e) => setMaxActions(parseInt(e.target.value) || 1)}
            className={inputCls}
          />
        </Field>
      </div>
      <CommonOptions v={common} onChange={setCommon} />
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          disabled={busy}
          onClick={() =>
            onSubmit({ engage_action: engageAction, max_actions: maxActions, ...common })
          }
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold uppercase tracking-widest transition-all disabled:opacity-50"
        >
          {busy ? "Launching…" : "Run engagement"}
        </button>
        <ClearDefaultsButton onClear={onClearDefaults} />
      </div>
    </div>
  );
}

function PursueForm({
  common,
  setCommon,
  onSubmit,
  busy,
  defaults,
  patchDefaults,
  onClearDefaults,
}: FormPersistenceProps) {
  const [profileName, setProfileName] = useState(
    defaults.pursue_profile_name ?? ""
  );
  const [maxPosts, setMaxPosts] = useState(defaults.pursue_max_posts ?? 3);
  const [perspectives, setPerspectives] = useState(
    defaults.pursue_perspectives ?? "insightful,professional"
  );
  const [bioKeywords, setBioKeywords] = useState(
    defaults.pursue_bio_keywords ?? ""
  );
  const [doFollow, setDoFollow] = useState(defaults.pursue_do_follow ?? true);
  const [doLike, setDoLike] = useState(defaults.pursue_do_like ?? true);
  const [doComment, setDoComment] = useState(defaults.pursue_do_comment ?? true);

  useEffect(() => {
    patchDefaults({
      pursue_profile_name: profileName,
      pursue_max_posts: maxPosts,
      pursue_perspectives: perspectives,
      pursue_bio_keywords: bioKeywords,
      pursue_do_follow: doFollow,
      pursue_do_like: doLike,
      pursue_do_comment: doComment,
    });
  }, [
    profileName,
    maxPosts,
    perspectives,
    bioKeywords,
    doFollow,
    doLike,
    doComment,
    patchDefaults,
  ]);

  const splitList = (s: string) =>
    s
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);

  return (
    <div className="space-y-4">
      <Field label="Profile name" hint="Search-visible LinkedIn name">
        <input
          value={profileName}
          onChange={(e) => setProfileName(e.target.value)}
          placeholder="Lara Acosta"
          className={inputCls}
        />
      </Field>
      <div className="grid sm:grid-cols-2 gap-3">
        <Field label="Max posts">
          <input
            type="number"
            min={1}
            max={20}
            value={maxPosts}
            onChange={(e) => setMaxPosts(parseInt(e.target.value) || 1)}
            className={inputCls}
          />
        </Field>
        <Field label="Perspectives" hint="Comma-separated">
          <input
            value={perspectives}
            onChange={(e) => setPerspectives(e.target.value)}
            placeholder="insightful, funny, motivational"
            className={inputCls}
          />
        </Field>
        <Field label="Bio keywords" hint="Optional, comma-separated">
          <input
            value={bioKeywords}
            onChange={(e) => setBioKeywords(e.target.value)}
            placeholder="investor, venture"
            className={inputCls}
          />
        </Field>
      </div>
      <div className="grid grid-cols-3 gap-3 p-3 rounded-lg bg-zinc-900/40 border border-zinc-900">
        <label className="flex items-center gap-2 text-[10px] font-bold text-zinc-500 uppercase tracking-widest cursor-pointer">
          <input
            type="checkbox"
            checked={doFollow}
            onChange={(e) => setDoFollow(e.target.checked)}
            className="size-3.5 rounded accent-blue-600"
          />
          Follow
        </label>
        <label className="flex items-center gap-2 text-[10px] font-bold text-zinc-500 uppercase tracking-widest cursor-pointer">
          <input
            type="checkbox"
            checked={doLike}
            onChange={(e) => setDoLike(e.target.checked)}
            className="size-3.5 rounded accent-blue-600"
          />
          Like
        </label>
        <label className="flex items-center gap-2 text-[10px] font-bold text-zinc-500 uppercase tracking-widest cursor-pointer">
          <input
            type="checkbox"
            checked={doComment}
            onChange={(e) => setDoComment(e.target.checked)}
            className="size-3.5 rounded accent-blue-600"
          />
          Comment
        </label>
      </div>
      <CommonOptions v={common} onChange={setCommon} />
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          disabled={busy || !profileName.trim()}
          onClick={() =>
            onSubmit({
              profile_name: profileName.trim(),
              max_posts: maxPosts,
              perspectives: splitList(perspectives),
              bio_keywords: bioKeywords ? splitList(bioKeywords) : undefined,
              should_follow: doFollow,
              should_like: doLike,
              should_comment: doComment,
              ...common,
            })
          }
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold uppercase tracking-widest transition-all disabled:opacity-50"
        >
          {busy ? "Launching…" : "Pursue profile"}
        </button>
        <ClearDefaultsButton onClear={onClearDefaults} />
      </div>
    </div>
  );
}

function CalendarForm({
  common,
  setCommon,
  onSubmit,
  busy,
  defaults,
  patchDefaults,
  onClearDefaults,
}: FormPersistenceProps) {
  const [niche, setNiche] = useState(defaults.calendar_niche ?? "");
  const [totalPosts, setTotalPosts] = useState(defaults.calendar_total_posts ?? 30);
  const [output, setOutput] = useState(defaults.calendar_output ?? "");

  useEffect(() => {
    patchDefaults({
      calendar_niche: niche,
      calendar_total_posts: totalPosts,
      calendar_output: output,
    });
  }, [niche, totalPosts, output, patchDefaults]);

  return (
    <div className="space-y-4">
      <Field label="Niche" hint="Industry or topic">
        <input
          value={niche}
          onChange={(e) => setNiche(e.target.value)}
          placeholder="fitness"
          className={inputCls}
        />
      </Field>
      <div className="grid sm:grid-cols-2 gap-3">
        <Field label="Total posts">
          <input
            type="number"
            min={1}
            max={365}
            value={totalPosts}
            onChange={(e) => setTotalPosts(parseInt(e.target.value) || 1)}
            className={inputCls}
          />
        </Field>
        <Field label="Output file" hint="Optional, defaults to content_calendar.txt">
          <input
            value={output}
            onChange={(e) => setOutput(e.target.value)}
            placeholder="content_calendar.txt"
            className={inputCls}
          />
        </Field>
      </div>
      <CommonOptions v={common} onChange={setCommon} />
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          disabled={busy || !niche.trim()}
          onClick={() =>
            onSubmit({
              niche: niche.trim(),
              total_posts: totalPosts,
              output: output || undefined,
              ...common,
            })
          }
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold uppercase tracking-widest transition-all disabled:opacity-50"
        >
          {busy ? "Launching…" : "Generate calendar"}
        </button>
        <ClearDefaultsButton onClear={onClearDefaults} />
      </div>
    </div>
  );
}

function SettingsForm({
  flash,
}: {
  flash: (m: Message) => void;
}) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [s, setS] = useState<FrameworkSettings>({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/config`);
      if (res.ok) setS(await res.json());
    } catch {
      flash({ type: "error", text: "Could not load framework settings." });
    } finally {
      setLoading(false);
    }
  }, [flash]);

  useEffect(() => {
    load();
  }, [load]);

  const set = <K extends keyof FrameworkSettings>(k: K, v: FrameworkSettings[K]) =>
    setS((prev) => ({ ...prev, [k]: v }));

  const save = async () => {
    setSaving(true);
    try {
      const payload: FrameworkSettings = { ...s };
      // Don't overwrite a masked key value on the server.
      if (payload.openai_api_key === "set") delete payload.openai_api_key;
      if (payload.gemini_api_key === "set") delete payload.gemini_api_key;
      const res = await fetch(`${API}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        flash({ type: "error", text: await parseErr(res) });
        return;
      }
      const j = await res.json();
      setS(j.settings || {});
      flash({ type: "success", text: "Settings saved." });
    } catch {
      flash({ type: "error", text: "Network error while saving settings." });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p className="text-[10px] text-zinc-500 uppercase tracking-widest">Loading…</p>;
  }

  const Toggle = ({
    label,
    val,
    onSet,
    hint,
  }: {
    label: string;
    val: boolean | null | undefined;
    onSet: (b: boolean) => void;
    hint?: string;
  }) => (
    <label className="flex items-start gap-3 p-3 rounded-lg bg-zinc-900/40 border border-zinc-900 cursor-pointer">
      <input
        type="checkbox"
        checked={!!val}
        onChange={(e) => onSet(e.target.checked)}
        className="size-3.5 rounded accent-blue-600 mt-0.5"
      />
      <div className="flex-1 min-w-0">
        <span className="block text-[10px] font-bold text-zinc-300 uppercase tracking-widest">
          {label}
        </span>
        {hint && <span className="block text-[10px] text-zinc-500 mt-0.5">{hint}</span>}
      </div>
    </label>
  );

  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2">
          AI keys
        </h3>
        <p className="text-[10px] text-zinc-500 mb-3">
          Stored encrypted in the dashboard DB. Leave a masked field (<code>set</code>)
          alone to keep its current value.
        </p>
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="OpenAI API key" hint="Used for AI comments / engagement">
            <input
              value={s.openai_api_key || ""}
              onChange={(e) => set("openai_api_key", e.target.value)}
              placeholder="sk-…"
              className={inputCls}
              type="password"
            />
          </Field>
          <Field label="OpenAI model" hint="Default: gpt-4o-mini">
            <input
              value={s.openai_model || ""}
              onChange={(e) => set("openai_model", e.target.value)}
              placeholder="gpt-4o-mini"
              className={inputCls}
            />
          </Field>
          <Field label="Gemini API key" hint="Used for AI post generation">
            <input
              value={s.gemini_api_key || ""}
              onChange={(e) => set("gemini_api_key", e.target.value)}
              placeholder="AIza…"
              className={inputCls}
              type="password"
            />
          </Field>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-3">
        <Toggle
          label="Use Gemini for posts"
          val={s.use_gemini}
          onSet={(b) => set("use_gemini", b)}
          hint="Falls back to OpenAI / templates if disabled or unavailable."
        />
        <Toggle
          label="Run browser headless"
          val={s.headless}
          onSet={(b) => set("headless", b)}
          hint="Disable to watch the bot work (slower, but easier to debug)."
        />
      </div>

      <div>
        <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2">
          Marketing mode
        </h3>
        <p className="text-[10px] text-zinc-500 mb-3">
          Appends a promotional tail to AI-generated posts and comments referencing your
          project. Leave fields blank to use framework defaults.
        </p>
        <div className="space-y-3">
          <Toggle
            label="Enable marketing tails"
            val={s.marketing_mode}
            onSet={(b) => set("marketing_mode", b)}
          />
          <div className="grid sm:grid-cols-2 gap-3">
            <Field label="Project name">
              <input
                value={s.project_name || ""}
                onChange={(e) => set("project_name", e.target.value)}
                className={inputCls}
              />
            </Field>
            <Field label="Project URL">
              <input
                value={s.project_url || ""}
                onChange={(e) => set("project_url", e.target.value)}
                className={inputCls}
              />
            </Field>
          </div>
          <Field label="Short pitch" hint="One-line description shown in comments">
            <input
              value={s.project_short_pitch || ""}
              onChange={(e) => set("project_short_pitch", e.target.value)}
              className={inputCls}
            />
          </Field>
          <Field label="Full pitch" hint="Used by AI for longer engagement">
            <textarea
              value={s.project_pitch || ""}
              onChange={(e) => set("project_pitch", e.target.value)}
              rows={3}
              className={`${inputCls} resize-none`}
            />
          </Field>
          <Field label="Tagline">
            <input
              value={s.project_tagline || ""}
              onChange={(e) => set("project_tagline", e.target.value)}
              className={inputCls}
            />
          </Field>
        </div>
      </div>

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={load}
          disabled={saving}
          className="px-4 py-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 text-[11px] font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all disabled:opacity-50"
        >
          Discard
        </button>
        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-bold uppercase tracking-widest transition-all disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save settings"}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AutomationPage() {
  const { data: session } = useSession();
  const userId = session?.user?.email || "local-user";

  const [tab, setTab] = useState<Tab>("post");
  const [common, setCommon] = useState<CommonState>(COMMON_DEFAULT);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Message | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [openTask, setOpenTask] = useState<Task | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [health, setHealth] = useState<{
    framework_available?: boolean;
    main_py_exists?: boolean;
    shared_cookie_exists?: boolean;
  }>({});
  // LinkedIn accounts the bot can run as. `selectedAccount === ""` means
  // "use the primary account" (whatever the backend's dashboard secrets
  // currently designate as primary).
  const [accountsPayload, setAccountsPayload] = useState<AccountsPayload>({
    accounts: [],
    active: null,
  });
  const [selectedAccount, setSelectedAccount] = useState<string>("");
  // Server-persisted dashboard form values. ``defaultsLoaded`` guards the
  // first-mount save effect — without it, the empty initial state would
  // immediately wipe the DB before /dashboard had a chance to return.
  const [formDefaults, setFormDefaults] = useState<FormDefaults>({});
  const [defaultsLoaded, setDefaultsLoaded] = useState(false);
  const lastSavedDefaultsRef = useRef<string>("");
  // Subscription plan — used purely to render the plan pill in the topbar
  // (mirrors /dashboard/billing). One-shot fetch on mount; plan rarely
  // changes inside a session.
  const [subscription, setSubscription] = useState<Subscription | null>(null);

  const endpoint = useMemo<Record<Tab, string>>(
    () => ({
      post: "/post",
      engage: "/engage",
      pursue: "/pursue",
      calendar: "/calendar",
      settings: "",
    }),
    []
  );

  const flash = useCallback((m: Message) => {
    setMessage(m);
    setTimeout(() => setMessage(null), 4000);
  }, []);

  const patchDefaults = useCallback((patch: Partial<FormDefaults>) => {
    setFormDefaults((prev) => {
      // Drop keys whose value didn't actually change to avoid pointless
      // re-renders and DB writes when a form re-emits the same slice.
      let changed = false;
      const next: FormDefaults = { ...prev };
      for (const [k, v] of Object.entries(patch)) {
        const key = k as keyof FormDefaults;
        if ((next[key] as unknown) !== v) {
          (next as Record<string, unknown>)[key] = v;
          changed = true;
        }
      }
      return changed ? next : prev;
    });
  }, []);

  // Wrap setters so user-driven changes also flow into formDefaults. The
  // debounced save effect (below) takes care of the round-trip to the DB.
  const setTabPersisted = useCallback(
    (t: Tab) => {
      setTab(t);
      patchDefaults({ tab: t });
    },
    [patchDefaults]
  );
  const setCommonPersisted = useCallback(
    (s: CommonState) => {
      setCommon(s);
      patchDefaults({
        common_debug: s.debug,
        common_headless: s.headless,
        common_no_ai: s.no_ai,
      });
    },
    [patchDefaults]
  );
  const setSelectedAccountPersisted = useCallback(
    (acc: string) => {
      setSelectedAccount(acc);
      patchDefaults({ selected_account: acc });
    },
    [patchDefaults]
  );

  // Single combined endpoint + ETag → 304 cuts roundtrips and bytes.
  // We track the last ETag and "anything running?" in refs so the polling
  // loop can read the latest value without restarting the interval.
  const etagRef = useRef<string | null>(null);
  const anyRunningRef = useRef(false);

  // ---------------------------------------------------------------------
  // Form defaults — load on first /dashboard response (above), debounce-
  // -save on any change, and clear by category. Each form receives a
  // ``patchDefaults`` setter and reads its initial values from
  // ``formDefaults``.
  // ---------------------------------------------------------------------

  // Debounced save: any change to formDefaults flushes to the DB after a
  // short idle window. Skipped until the initial load completes so an
  // empty hydration state can't wipe stored values on mount.
  useEffect(() => {
    if (!defaultsLoaded) return;
    const serialized = JSON.stringify(formDefaults);
    if (serialized === lastSavedDefaultsRef.current) return;
    const timer = setTimeout(() => {
      lastSavedDefaultsRef.current = serialized;
      fetch(`${API}/form-defaults`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: serialized,
      }).catch(() => {
        // Soft failure — the user just won't see persistence on this
        // edit. We don't surface a toast because every keystroke would
        // potentially trigger it.
      });
    }, 500);
    return () => clearTimeout(timer);
  }, [formDefaults, defaultsLoaded]);

  const clearDefaults = useCallback(
    async (prefix: string) => {
      try {
        const url = prefix
          ? `${API}/form-defaults?prefix=${encodeURIComponent(prefix)}`
          : `${API}/form-defaults`;
        const res = await fetch(url, { method: "DELETE" });
        if (!res.ok) {
          flash({ type: "error", text: await parseErr(res) });
          return;
        }
        setFormDefaults((prev) => {
          const next: FormDefaults = { ...prev };
          for (const k of Object.keys(prev)) {
            if (!prefix || k.startsWith(prefix)) {
              delete (next as Record<string, unknown>)[k];
            }
          }
          lastSavedDefaultsRef.current = JSON.stringify(next);
          return next;
        });
        flash({ type: "success", text: "Saved defaults cleared." });
      } catch {
        flash({ type: "error", text: "Network error clearing defaults." });
      }
    },
    [flash]
  );

  const refresh = useCallback(async () => {
    setTasksLoading(true);
    try {
      const headers: Record<string, string> = {};
      if (etagRef.current) headers["If-None-Match"] = etagRef.current;
      const res = await fetch(
        `${API}/dashboard?limit=25&user_id=${encodeURIComponent(userId)}`,
        { headers }
      );
      if (res.status === 304) {
        // Nothing changed — skip state updates entirely.
        return;
      }
      if (!res.ok) return;
      const newEtag = res.headers.get("ETag");
      if (newEtag) etagRef.current = newEtag;
      const j = await res.json();
      const nextTasks = (j.tasks as Task[]) || [];
      setTasks(nextTasks);
      setStats((j.stats as Stats) || null);
      setHealth(j.health || {});
      if (j.accounts) setAccountsPayload(j.accounts as AccountsPayload);
      // Hydrate the form-defaults blob only once — after the first server
      // response. Subsequent polls just refresh stats/tasks; the user is
      // typing into the forms by then and we don't want to clobber input.
      if (j.form_defaults && !defaultsLoaded) {
        const fd = j.form_defaults as FormDefaults;
        setFormDefaults(fd);
        lastSavedDefaultsRef.current = JSON.stringify(fd);
        if (typeof fd.tab === "string") setTab(fd.tab);
        if (typeof fd.selected_account === "string") {
          setSelectedAccount(fd.selected_account);
        }
        if (
          typeof fd.common_debug === "boolean" ||
          typeof fd.common_headless === "boolean" ||
          fd.common_headless === null ||
          typeof fd.common_no_ai === "boolean"
        ) {
          setCommon((prev) => ({
            debug: fd.common_debug ?? prev.debug,
            headless:
              fd.common_headless === undefined ? prev.headless : fd.common_headless,
            no_ai: fd.common_no_ai ?? prev.no_ai,
          }));
        }
        setDefaultsLoaded(true);
      }
      anyRunningRef.current = nextTasks.some((t) => t.running);
    } catch {
      /* offline */
    } finally {
      setTasksLoading(false);
    }
  }, [userId]);

  // Reset the ETag when the user changes — payload contents are user-scoped.
  useEffect(() => {
    etagRef.current = null;
  }, [userId]);

  // Plan pill — one-shot fetch when the user changes. /api/billing/subscription
  // applies the local-user/admin → agency override server-side, so the pill
  // here matches what /dashboard/billing renders.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `${BILLING_API}/subscription?user_id=${encodeURIComponent(userId)}`
        );
        if (!cancelled && res.ok) {
          setSubscription((await res.json()) as Subscription);
        }
      } catch {
        /* Pill is purely decorative; silently fall back to no pill. */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  // Adaptive polling: fast (3s) while something is running, slow (30s) when
  // idle, paused entirely while the tab is hidden. Resumes immediately on
  // `visibilitychange` so the user never sees stale data on tab return.
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const schedule = () => {
      if (cancelled) return;
      const interval =
        document.visibilityState === "hidden"
          ? 60000
          : anyRunningRef.current
            ? 3000
            : 30000;
      timer = setTimeout(tick, interval);
    };

    const tick = async () => {
      if (cancelled) return;
      if (document.visibilityState === "visible") {
        await refresh();
      }
      schedule();
    };

    const onVisibility = () => {
      if (document.visibilityState === "visible" && !cancelled) {
        if (timer) clearTimeout(timer);
        tick();
      }
    };

    tick();
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [refresh]);

  const submit = useCallback(
    async (body: Record<string, unknown>) => {
      if (busy || !endpoint[tab]) return;
      const cleaned: Record<string, unknown> = { user_id: userId };
      if (selectedAccount) cleaned.account = selectedAccount;
      Object.entries(body).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") cleaned[k] = v;
      });
      setBusy(true);
      try {
        const res = await fetch(`${API}${endpoint[tab]}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(cleaned),
        });
        if (!res.ok) {
          flash({ type: "error", text: await parseErr(res) });
          return;
        }
        const j = await res.json();
        flash({ type: "success", text: `Task ${j.id} launched.` });
        // Force a body refresh (new task should always be visible) by
        // dropping the cached ETag before the immediate poll.
        etagRef.current = null;
        refresh();
      } catch {
        flash({ type: "error", text: "Network error. Is the backend running?" });
      } finally {
        setBusy(false);
      }
    },
    [busy, endpoint, flash, refresh, selectedAccount, tab, userId]
  );

  const stopTask = async (id: string) => {
    try {
      const res = await fetch(`${API}/tasks/${id}/stop`, { method: "POST" });
      if (res.ok) {
        flash({ type: "success", text: `Task ${id} stopped.` });
        etagRef.current = null;
        refresh();
      } else {
        flash({ type: "error", text: await parseErr(res) });
      }
    } catch {
      flash({ type: "error", text: "Network error stopping task." });
    }
  };

  const viewTask = async (id: string) => {
    try {
      const res = await fetch(`${API}/tasks/${id}?log_lines=500`);
      if (res.ok) setOpenTask(await res.json());
      else flash({ type: "error", text: await parseErr(res) });
    } catch {
      flash({ type: "error", text: "Network error fetching task." });
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-400 font-sans selection:bg-blue-600/20">
      <nav className="sticky top-0 z-[110] bg-zinc-950/80 backdrop-blur-md border-b border-zinc-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-12 items-center">
            <div className="flex items-center gap-3 min-w-0">
              <Link
                href="/dashboard"
                className="font-serif text-base font-bold tracking-tight bg-gradient-to-r from-indigo-300 via-blue-300 to-violet-300 bg-clip-text text-transparent hover:opacity-80 transition-opacity"
              >
                LinkdApply
              </Link>
              {subscription && <PlanPill plan={subscription.plan} />}
            </div>
            <div className="flex items-center space-x-6">
              <Link
                href="/dashboard"
                className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest hover:text-white transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/dashboard/automation"
                className="text-[10px] font-bold text-white uppercase tracking-widest"
              >
                Automation
              </Link>
              <Link
                href="/dashboard/billing"
                className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest hover:text-white transition-colors"
              >
                Billing
              </Link>
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800">
                <div
                  className={`size-1.5 rounded-full ${
                    health.framework_available ? "bg-emerald-500" : "bg-red-500"
                  }`}
                />
                <span className="text-[10px] font-medium text-zinc-400 uppercase tracking-tighter">
                  Framework {health.framework_available ? "Ready" : "Missing"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-4">
            <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest mb-1">
              Today
            </p>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-white tracking-tight">
                {stats?.daily_used ?? 0}
              </span>
              <span className="text-xs text-zinc-600">
                / {stats?.daily_limit ?? "?"}
              </span>
            </div>
            <div className="mt-2 h-1 w-full bg-zinc-900 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all duration-700"
                style={{
                  width: `${Math.min(
                    100,
                    stats && stats.daily_limit > 0
                      ? (stats.daily_used / stats.daily_limit) * 100
                      : 0
                  )}%`,
                }}
              />
            </div>
            <p className="text-[9px] text-zinc-600 mt-1">
              Plan:{" "}
              <span className="text-zinc-400 uppercase">{stats?.plan ?? "—"}</span>
            </p>
          </div>
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-4">
            <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest mb-1">
              Last 30 days
            </p>
            <p className="text-2xl font-bold text-white tracking-tight">
              {stats?.last_30d ?? 0}
            </p>
            <p className="text-[9px] text-zinc-600 mt-2">
              {Object.entries(stats?.by_action_30d ?? {})
                .map(([a, n]) => `${a} ${n}`)
                .join(" · ") || "No activity"}
            </p>
          </div>
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-4">
            <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest mb-1">
              Outcomes (30d)
            </p>
            <div className="flex gap-3 text-[10px]">
              <span className="text-emerald-400">
                ✓ {stats?.by_status_30d?.completed ?? 0}
              </span>
              <span className="text-amber-400">
                ⏸ {stats?.by_status_30d?.stopped ?? 0}
              </span>
              <span className="text-red-400">
                ✕ {stats?.by_status_30d?.failed ?? 0}
              </span>
            </div>
            <p className="text-[9px] text-zinc-600 mt-2">
              All-time: <span className="text-zinc-400">{stats?.total_all_time ?? 0}</span>
            </p>
          </div>
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-4">
            <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest mb-1">
              Running now
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white tracking-tight">
                {stats?.running ?? 0}
              </span>
              {(stats?.running ?? 0) > 0 && (
                <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
              )}
            </div>
            <p className="text-[9px] text-zinc-600 mt-2">
              Active subprocesses tracked by the backend.
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4 grid lg:grid-cols-12 gap-6">
        <section className="lg:col-span-5">
          {accountsPayload.accounts.length > 0 && tab !== "settings" && (
            <div className="bg-zinc-950 border border-zinc-900 rounded-xl shadow-sm mb-4 px-4 py-3 flex items-center gap-3">
              <div className="shrink-0">
                <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">
                  Running as
                </p>
                <p className="text-[10px] text-zinc-600 mt-0.5">
                  LinkedIn account this task will authenticate as
                </p>
              </div>
              <div className="flex-1">
                {accountsPayload.accounts.length === 1 ? (
                  <p className="text-xs font-mono text-zinc-300">
                    {accountsPayload.accounts[0].username}
                    <span className="ml-2 text-[9px] text-emerald-500 uppercase tracking-widest font-bold">
                      primary
                    </span>
                  </p>
                ) : (
                  <select
                    value={selectedAccount}
                    onChange={(e) => setSelectedAccountPersisted(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 text-zinc-200 text-xs rounded px-2 py-1.5 focus:outline-none focus:border-blue-500 font-mono"
                  >
                    <option value="">
                      Primary (
                      {accountsPayload.active || "not configured"}
                      )
                    </option>
                    {accountsPayload.accounts
                      .filter((a) => !a.primary)
                      .map((a) => (
                        <option key={a.username} value={a.username}>
                          {a.username}
                        </option>
                      ))}
                  </select>
                )}
              </div>
            </div>
          )}
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl shadow-sm overflow-hidden">
            <div className="px-4 py-2 border-b border-zinc-900 bg-zinc-900/30 flex gap-1">
              {TABS.map((t) => (
                <button
                  key={t}
                  onClick={() => setTabPersisted(t)}
                  className={`px-3 py-1 text-[10px] font-bold uppercase tracking-widest rounded transition-all ${
                    tab === t
                      ? "bg-blue-600 text-white"
                      : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
            <div className="p-4">
              {tab === "post" && (
                <PostForm
                  common={common}
                  setCommon={setCommonPersisted}
                  onSubmit={submit}
                  busy={busy}
                  defaults={formDefaults}
                  patchDefaults={patchDefaults}
                  onClearDefaults={() => clearDefaults("post_")}
                />
              )}
              {tab === "engage" && (
                <EngageForm
                  common={common}
                  setCommon={setCommonPersisted}
                  onSubmit={submit}
                  busy={busy}
                  defaults={formDefaults}
                  patchDefaults={patchDefaults}
                  onClearDefaults={() => clearDefaults("engage_")}
                />
              )}
              {tab === "pursue" && (
                <PursueForm
                  common={common}
                  setCommon={setCommonPersisted}
                  onSubmit={submit}
                  busy={busy}
                  defaults={formDefaults}
                  patchDefaults={patchDefaults}
                  onClearDefaults={() => clearDefaults("pursue_")}
                />
              )}
              {tab === "calendar" && (
                <CalendarForm
                  common={common}
                  setCommon={setCommonPersisted}
                  onSubmit={submit}
                  busy={busy}
                  defaults={formDefaults}
                  patchDefaults={patchDefaults}
                  onClearDefaults={() => clearDefaults("calendar_")}
                />
              )}
              {tab === "settings" && <SettingsForm flash={flash} />}
            </div>
          </div>

          <div className="mt-4 bg-zinc-950 border border-zinc-900 rounded-xl p-3 text-[10px] text-zinc-500 space-y-1">
            <p>
              <span className="text-zinc-400 font-bold uppercase tracking-widest">Note —</span>{" "}
              Credentials are shared with the job applier via the dashboard secrets, and the
              same LinkedIn cookie file is reused.
            </p>
            {!health.shared_cookie_exists && (
              <p className="text-amber-400/80">
                No cached LinkedIn cookie yet; the first run will log in and create one.
              </p>
            )}
          </div>
        </section>

        <section className="lg:col-span-7">
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl shadow-sm overflow-hidden">
            <div className="px-4 py-3 bg-zinc-900/50 border-b border-zinc-900 flex items-center justify-between">
              <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                Tasks
                {tasks.some((t) => t.running) && (
                  <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
                )}
              </h2>
              <button
                onClick={() => {
                  etagRef.current = null;
                  refresh();
                }}
                disabled={tasksLoading}
                className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest hover:text-white transition-colors disabled:opacity-50"
              >
                Refresh
              </button>
            </div>
            <div className="overflow-x-auto max-h-[600px]">
              <table className="w-full text-left">
                <thead className="sticky top-0 bg-zinc-950 z-10">
                  <tr className="border-b border-zinc-900">
                    <th className="px-4 py-3 text-[9px] font-bold text-zinc-500 uppercase tracking-wider">
                      Task
                    </th>
                    <th className="px-4 py-3 text-[9px] font-bold text-zinc-500 uppercase tracking-wider">
                      Account
                    </th>
                    <th className="px-4 py-3 text-[9px] font-bold text-zinc-500 uppercase tracking-wider">
                      Started
                    </th>
                    <th className="px-4 py-3 text-[9px] font-bold text-zinc-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-[9px] font-bold text-zinc-500 uppercase tracking-wider text-right">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900">
                  {tasks.length > 0 ? (
                    tasks.map((t) => (
                      <tr key={t.id} className="hover:bg-zinc-900/20 transition-colors">
                        <td className="px-4 py-3">
                          <p className="text-xs font-semibold text-zinc-300 capitalize">
                            {t.action.replace("-", " ")}
                          </p>
                          <p className="text-[9px] text-zinc-600 font-mono">{t.id}</p>
                        </td>
                        <td className="px-4 py-3 text-[10px] text-zinc-400 font-mono">
                          {t.account_username || (
                            <span className="text-zinc-700">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-[10px] text-zinc-500">
                          {fmtTime(t.started_at)}
                        </td>
                        <td className="px-4 py-3">
                          <StatusPill task={t} />
                          {t.exit_code !== null && t.exit_code !== undefined && (
                            <p className="text-[9px] text-zinc-600 mt-0.5">
                              exit {t.exit_code}
                            </p>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="inline-flex gap-1">
                            <button
                              onClick={() => viewTask(t.id)}
                              className="px-2 py-1 rounded bg-zinc-900 border border-zinc-800 text-[9px] font-bold text-zinc-300 uppercase tracking-wider hover:bg-zinc-800"
                            >
                              Logs
                            </button>
                            {t.running && (
                              <button
                                onClick={() => stopTask(t.id)}
                                className="px-2 py-1 rounded bg-red-600/20 border border-red-500/30 text-[9px] font-bold text-red-300 uppercase tracking-wider hover:bg-red-600/30"
                              >
                                Stop
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-4 py-10 text-center text-zinc-600 text-[10px] uppercase tracking-widest"
                      >
                        No tasks yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>

      {openTask && (
        <div className="fixed inset-0 z-[220] flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
              <div className="min-w-0">
                <p className="text-xs font-bold text-zinc-300 capitalize">
                  {openTask.action.replace("-", " ")}{" "}
                  <span className="text-zinc-600 font-mono text-[10px]">{openTask.id}</span>
                </p>
                <p className="text-[10px] text-zinc-500 mt-0.5">
                  Started {fmtTime(openTask.started_at)}
                  {openTask.ended_at ? ` • ended ${fmtTime(openTask.ended_at)}` : ""}
                  {openTask.exit_code !== null && openTask.exit_code !== undefined
                    ? ` • exit ${openTask.exit_code}`
                    : ""}
                </p>
                {openTask.account_username && (
                  <p className="text-[10px] text-zinc-400 font-mono mt-0.5">
                    Account: {openTask.account_username}
                  </p>
                )}
              </div>
              <button
                onClick={() => setOpenTask(null)}
                className="text-zinc-500 hover:text-white p-1 rounded"
                aria-label="Close"
              >
                <svg
                  className="size-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <pre className="whitespace-pre-wrap break-words text-[11px] leading-relaxed text-zinc-300 font-mono">
                {openTask.log || "(empty)"}
              </pre>
            </div>
            <div className="px-4 py-3 border-t border-zinc-800 flex justify-end gap-2">
              <button
                onClick={() => viewTask(openTask.id)}
                className="px-3 py-1.5 rounded-md bg-zinc-900 border border-zinc-800 text-[10px] font-bold text-zinc-300 uppercase tracking-widest hover:bg-zinc-800"
              >
                Refresh
              </button>
              {openTask.running && (
                <button
                  onClick={() => stopTask(openTask.id)}
                  className="px-3 py-1.5 rounded-md bg-red-600/20 border border-red-500/30 text-[10px] font-bold text-red-300 uppercase tracking-widest hover:bg-red-600/30"
                >
                  Stop task
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {message && (
        <div className="fixed bottom-6 right-6 z-[100] animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div
            className={`pl-4 pr-2 py-2 rounded-lg flex items-center gap-4 shadow-2xl border backdrop-blur-xl ${
              message.type === "success"
                ? "bg-zinc-950/90 border-emerald-500/20 text-emerald-400"
                : message.type === "warning"
                  ? "bg-zinc-950/90 border-amber-500/20 text-amber-400"
                  : "bg-zinc-950/90 border-red-500/20 text-red-400"
            }`}
          >
            <div className="flex items-center gap-3">
              <div
                className={`size-1.5 rounded-full animate-pulse ${
                  message.type === "success"
                    ? "bg-emerald-500"
                    : message.type === "warning"
                      ? "bg-amber-500"
                      : "bg-red-500"
                }`}
              />
              <p className="text-[11px] font-medium text-zinc-300 pr-2 border-r border-zinc-800">
                {message.text}
              </p>
              <button
                onClick={() => setMessage(null)}
                className="size-6 rounded flex items-center justify-center hover:bg-zinc-900 transition-colors"
                aria-label="Dismiss"
              >
                <svg
                  className="size-3 opacity-40 hover:opacity-100"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
