"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import PersonalsForm from "@/components/PersonalsForm";
import SearchForm from "@/components/SearchForm";
import SettingsForm from "@/components/SettingsForm";
import QuestionsForm from "@/components/QuestionsForm";
import SecretsForm from "@/components/SecretsForm";
import { apiFetch, encodeUserId } from "@/lib/desktop-api";
import {
  formatConfigContent,
  parseConfigContent,
} from "@/lib/config-parse";

const CONFIG_FILES = ["personals.py", "search.py", "settings.py", "questions.py", "secrets.py"];

type ActivitySnapshot = {
  company?: string | null;
  job_title?: string | null;
  timestamp?: string | null;
  reason?: string | null;
};

async function parseApiError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    const d = data?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return d.map((x: { msg?: string }) => x?.msg || "").filter(Boolean).join("; ") || res.statusText;
    return res.statusText || "Request failed";
  } catch {
    return res.statusText || "Request failed";
  }
}

function formatShortTime(iso: string | null | undefined) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}

function formatPeriodEnd(value: unknown): string {
  if (value === null || value === undefined) return "—";
  try {
    if (typeof value === "number") {
      return new Date(value * 1000).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
    }
    return new Date(String(value)).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return String(value);
  }
}

function getSubAccess(sub: { plan?: string; status?: string } | null) {
  if (!sub) {
    return { canApply: false, isTrial: false, isExpiredTrial: false, needsUpgrade: true };
  }
  const status = String(sub.status || "").toLowerCase();
  const plan = String(sub.plan || "").toLowerCase();
  const canApply = status === "active" || status === "trialing";
  const isTrial = plan === "free_trial" && status === "trialing";
  const isExpiredTrial =
    plan === "free_trial" && (status === "expired" || status === "inactive");
  return { canApply, isTrial, isExpiredTrial, needsUpgrade: !canApply };
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState(CONFIG_FILES[0]);
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning', text: string } | null>(null);
  const [botStatus, setBotStatus] = useState<"running" | "stopped" | "error" | "paused">("stopped");
  const [appliedCount, setAppliedCount] = useState<number>(0);
  const [applyLimit, setApplyLimit] = useState<number>(0);
  const [botSpeed, setBotSpeed] = useState<number>(5);
  const [resumeName, setResumeName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isBackendHealthy, setIsBackendHealthy] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [subscription, setSubscription] = useState<any>(null);
  const [subscriptionKnown, setSubscriptionKnown] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isFormMode, setIsFormMode] = useState(true);
  const [formData, setFormData] = useState<Record<string, any>>({});
  /** Skip content→form parse when form mode just wrote content (prevents focus loss). */
  const formWroteContentRef = useRef(false);
  const [lastApplied, setLastApplied] = useState<ActivitySnapshot | null>(null);
  const [lastFailed, setLastFailed] = useState<ActivitySnapshot | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [logsCopied, setLogsCopied] = useState(false);
  const [logsPayload, setLogsPayload] = useState<{
    logs: string;
    log_dir?: string;
    run_id?: number | null;
    files?: { filename: string; path: string; size_bytes: number; modified_utc: string }[];
    infra?: { title: string; filename: string; content: string }[];
    profiles?: { id: string; filename: string; content: string }[];
  } | null>(null);
  const [logsLoading, setLogsLoading] = useState(false);
  const [botRuns, setBotRuns] = useState<
    { id: number; status?: string; start_time?: string; has_logs?: boolean }[]
  >([]);
  const [selectedLogRunId, setSelectedLogRunId] = useState<number | "">("");
  const { data: session, status } = useSession();
  const router = useRouter();

  const userId = session?.user?.email;

  const formEntriesForTab = useCallback(
    (data: Record<string, any>) => Object.entries(data),
    []
  );

  useEffect(() => {
    if (!userId) return;
    fetchConfig(activeTab);
  }, [activeTab, userId]);

  const loadBotLogs = useCallback(
    async (runId?: number | "") => {
      setLogsLoading(true);
      try {
        const runParam =
          runId !== undefined && runId !== "" ? `&run_id=${runId}` : "";
        const res = await apiFetch(
          `/api/bot/logs?lines=200&user_id=${encodeUserId(userId)}${runParam}`
        );
        if (res.ok) {
          setLogsPayload(await res.json());
        } else {
          setLogsPayload({ logs: await parseApiError(res) });
        }
      } catch {
        setLogsPayload({ logs: "Could not load logs. Is the backend running?" });
      } finally {
        setLogsLoading(false);
      }
    },
    [userId]
  );

  const openLogsModal = useCallback(async () => {
    setShowLogsModal(true);
    setLogsPayload(null);
    let initialRun: number | "" = "";
    try {
      const runsRes = await apiFetch(
        `/api/bot/runs?limit=15&user_id=${encodeUserId(userId)}`
      );
      if (runsRes.ok) {
        const data = await runsRes.json();
        const runs = Array.isArray(data.runs) ? data.runs : [];
        setBotRuns(runs);
        const withLogs = runs.find((r: { has_logs?: boolean }) => r.has_logs);
        const pick = withLogs ?? runs[0];
        if (pick?.id != null) {
          initialRun = pick.id;
          setSelectedLogRunId(pick.id);
        }
      }
    } catch {
      setBotRuns([]);
    }
    await loadBotLogs(initialRun);
  }, [userId, loadBotLogs]);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await apiFetch(`/api/bot/status?user_id=${encodeUserId(userId)}`);
        if (res.ok) {
          const data = await res.json();
          setBotStatus(data.status);
          if (data.applied_count !== undefined) setAppliedCount(data.applied_count);
          if (data.limit !== undefined) setApplyLimit(data.limit);
          setLastApplied(data.last_applied ?? null);
          setLastFailed(data.last_failed ?? null);
          setIsBackendHealthy(true);
        } else {
          setIsBackendHealthy(false);
        }
      } catch {
        setBotStatus("error");
        setIsBackendHealthy(false);
      }
    };

    const fetchResumeInfo = async () => {
        try {
            const res = await apiFetch(`/api/config/questions?user_id=${encodeUserId(userId)}`);
            const data = await res.json();
            const match = data.content.match(/default_resume_path = "(.*)"/);
            if (match) setResumeName(match[1]);
        } catch {}
    };

    const fetchSubscription = async () => {
      const inactive = { plan: "free", status: "inactive", limit: 0 };
      try {
        const res = await fetch(
          `/api/billing/subscription?user_id=${encodeUserId(userId)}`,
          { credentials: "include" }
        );
        if (res.ok) {
          const data = await res.json();
          setSubscription(data);
        } else {
          // Still show upgrade/trial UI when billing API errors (desktop, 401, etc.)
          setSubscription(inactive);
        }
      } catch {
        console.error("Failed to fetch subscription");
        setSubscription(inactive);
      } finally {
        setSubscriptionKnown(true);
      }
    };

    const fetchBotSpeed = async () => {
      try {
        const res = await apiFetch(`/api/config/settings?user_id=${encodeUserId(userId)}`);
        const data = await res.json();
        const match = data.content.match(/bot_speed = (\d+)/);
        if (match) setBotSpeed(parseInt(match[1]));
      } catch {}
    };

    const fetchStats = async () => {
      try {
        const res = await apiFetch(`/api/applications/stats?user_id=${encodeUserId(userId)}`);
        if (res.ok) setStats(await res.json());
      } catch {}
    };

    const fetchHistory = async () => {
      try {
        const res = await apiFetch(`/api/applications/history?user_id=${encodeUserId(userId)}&limit=10`);
        if (res.ok) {
            const data = await res.json();
            setHistory(data.history);
        }
      } catch {}
    };

    if (status === "loading") return;

    checkStatus();
    fetchResumeInfo();
    fetchBotSpeed();
    fetchSubscription();
    fetchStats();
    fetchHistory();

    const statusInterval = setInterval(() => {
      checkStatus();
      fetchSubscription();
      fetchStats();
      fetchHistory();
    }, 10000);

    return () => clearInterval(statusInterval);
  }, [userId, status, router]);

  useEffect(() => {
    if (botStatus === "running" && isStarting) setIsStarting(false);
  }, [botStatus, isStarting]);

  // Live sync: Parse code content into formData whenever content changes
  useEffect(() => {
    if (!content) return;
    if (formWroteContentRef.current) {
      formWroteContentRef.current = false;
      return;
    }

    const parsed = parseConfigContent(content);

    if (JSON.stringify(parsed) !== JSON.stringify(formData)) {
      setFormData(parsed);
    }
  }, [content]);

  // Sync from Form -> Code
  useEffect(() => {
    if (!isFormMode || !activeTab) return;
    
    const category = activeTab.split(".")[0];
    let newContent = formatConfigContent(category, formData);
    
    if (newContent !== content) {
      formWroteContentRef.current = true;
      setContent(newContent);
    }
  }, [formData, isFormMode, activeTab]);

  const fetchConfig = async (filename: string) => {
    setIsLoading(true);
    setMessage(null);
    try {
      const cleanName = filename.split('.')[0];
      const res = await apiFetch(`/api/config/${cleanName}?user_id=${encodeUserId(userId)}`);
      if (!res.ok) throw new Error("Failed to fetch");
      const data = await res.json();
      setContent(data.content || "");
      setFormData(parseConfigContent(data.content || ""));
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Error loading configuration. Ensure backend is running.' });
      setContent("");
    } finally {
      setIsLoading(false);
    }
  };

  const saveConfig = async () => {
    setIsSaving(true);
    setMessage(null);

    let finalContent = content;

    // If we are in form mode, we need to regenerate the content string
    if (isFormMode) {
      const category = activeTab.split(".")[0];
      finalContent = formatConfigContent(category, formData);

    try {
      const cleanName = activeTab.split('.')[0];
      const res = await apiFetch(`/api/config/${cleanName}?user_id=${encodeUserId(userId)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: finalContent }),
      });
      if (!res.ok) throw new Error("Failed to save");
      setMessage({ type: 'success', text: 'Configuration saved successfully!' });
      setContent(finalContent);
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Error saving configuration.' });
    } finally {
      setIsSaving(false);
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const wait = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

  const startBot = async () => {
    setShowConfirm(false);
    if (isLoading || isStarting) return;
    setIsLoading(true);
    setIsStarting(true);
    setConnectionError(null);
    setMessage(null);
    try {
      const res = await apiFetch(`/api/bot/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });
      if (!res.ok) {
        setConnectionError(await parseApiError(res));
        setIsStarting(false);
        return;
      }
      const data = await res.json().catch(() => ({}));
      if (data.status === "already_running") {
        setBotStatus("running");
        setIsStarting(false);
        setMessage({ type: "success", text: "Bot is already running." });
        return;
      }
      for (let i = 0; i < 24; i++) {
        await wait(650);
        try {
          const st = await apiFetch(`/api/bot/status?user_id=${encodeUserId(userId)}`);
          if (st.ok) {
            const j = await st.json();
            setLastApplied(j.last_applied ?? null);
            setLastFailed(j.last_failed ?? null);
            if (j.applied_count !== undefined) setAppliedCount(j.applied_count);
            if (j.limit !== undefined) setApplyLimit(j.limit);
            if (j.status === "running") {
              setBotStatus("running");
              setIsStarting(false);
              setMessage({ type: "success", text: "Bot is running." });
              return;
            }
          }
        } catch {
          /* ignore single poll failure */
        }
      }
      setConnectionError("Could not confirm the bot started. Open logs to see supervisor output.");
      setIsStarting(false);
    } catch {
      setConnectionError("Network error while starting the bot.");
      setIsStarting(false);
    } finally {
      setIsLoading(false);
    }
  };

  const stopBot = async () => {
    if (isStopping) return;
    setIsStopping(true);
    setConnectionError(null);
    setMessage(null);
    try {
      const res = await apiFetch(`/api/bot/stop`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });
      if (!res.ok) {
        setConnectionError(await parseApiError(res));
        return;
      }
      const data = await res.json().catch(() => ({}));
      setBotStatus("stopped");
      setMessage({
        type: "success",
        text: data.status === "not_running" ? "Bot was not running." : "Bot stopped.",
      });
    } catch {
      setConnectionError("Network error while stopping the bot.");
    } finally {
      setIsStopping(false);
    }
  };

  const goToSettings = () => {
    setActiveTab("settings.py");
    document.getElementById("dashboard-configuration")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const subAccess = getSubAccess(subscription);
  const subActive = subAccess.canApply;
  const usageLimit = subscription?.limit ?? (subAccess.isTrial ? 10 : 0);
  const startDisabled =
    isLoading ||
    isStarting ||
    !isBackendHealthy ||
    !subActive ||
    botStatus === "running";
  const stopDisabled = isStopping || botStatus !== "running";
  const logsDisabled = !isBackendHealthy;

  const updateBotSpeed = async (speed: number) => {
    setBotSpeed(speed);
    try {
        const res = await apiFetch(`/api/config/settings?user_id=${encodeUserId(userId)}`);
        const data = await res.json();
        let newContent = data.content;
        
        if (newContent.includes("bot_speed =")) {
            newContent = newContent.replace(/bot_speed = \d+/, `bot_speed = ${speed}`);
        } else {
            newContent += `\nbot_speed = ${speed}`;
        }

        await apiFetch(`/api/config/settings?user_id=${encodeUserId(userId)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: newContent }),
        });
        
        setMessage({ type: 'success', text: `Speed updated to ${speed}x` });
    } catch (err) {
        setMessage({ type: 'error', text: 'Failed to update speed.' });
    }
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.type !== "application/pdf") {
        setMessage({ type: 'error', text: 'Please upload a PDF file.' });
        return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await apiFetch(`/api/upload/resume?user_id=${encodeUserId(userId)}`, {
            method: "POST",
            body: formData,
        });
        if (!res.ok) throw new Error("Upload failed");
        const data = await res.json();
        setResumeName(data.filename);
        setMessage({ type: 'success', text: 'Resume uploaded successfully!' });
    } catch (err) {
        setMessage({ type: 'error', text: 'Failed to upload resume.' });
    } finally {
        setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-400 font-sans selection:bg-blue-600/20">
      {/* Top Navbar */}
      {/* Slim Navigation */}
      <nav className="sticky top-0 z-[110] bg-zinc-950/80 backdrop-blur-md border-b border-zinc-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-12 items-center">
            <div className="flex items-center gap-3 min-w-0">
              <span className="font-serif text-base font-bold tracking-tight bg-gradient-to-r from-indigo-300 via-blue-300 to-violet-300 bg-clip-text text-transparent">
                LinkdApply
              </span>
              {subscription && (
                <div className="px-2 py-0.5 rounded border border-zinc-800 bg-zinc-900">
                  <span className={`text-[9px] font-bold uppercase tracking-wider ${
                    subscription.plan === 'pro' ? 'text-indigo-400' :
                    subscription.plan === 'agency' ? 'text-amber-400' :
                    subscription.plan === 'free_trial' ? 'text-amber-400' :
                    'text-zinc-500'
                  }`}>
                    {subscription.plan === 'free_trial' ? 'Free Trial' : subscription.plan}
                  </span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-6">
               <Link 
                  href="/dashboard/automation"
                  className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest hover:text-white transition-colors"
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
                  <div className={`size-1.5 rounded-full ${isBackendHealthy ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                  <span className="text-[10px] font-medium text-zinc-400 uppercase tracking-tighter">System {isBackendHealthy ? 'OK' : 'Error'}</span>
               </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Confirmation Modal */}
      {/* Confirmation Modal - Minimal */}
      {showConfirm && (
        <div className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 max-w-sm w-full shadow-2xl">
            <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-4">Start Automation</h3>
            
            <div className="space-y-4 mb-6">
              <div className="bg-amber-500/5 border border-amber-500/10 rounded-lg p-3">
                <p className="text-[10px] text-amber-500/80 font-bold uppercase tracking-tight mb-1">Compliance Warning</p>
                <p className="text-[11px] text-zinc-400 leading-relaxed">
                  Ensure your usage complies with LinkedIn's Terms of Service. Automated applications should be reviewed carefully. LinkdApply mimics human patterns, but you are responsible for your account health.
                </p>
              </div>
              <p className="text-[11px] text-zinc-500 leading-relaxed">
                The bot will launch Chrome and begin applying based on your configured limits and settings.
              </p>
            </div>

            <div className="flex gap-2">
              <button 
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-2 rounded-lg bg-zinc-900 text-zinc-400 text-[10px] font-bold uppercase tracking-widest hover:text-white transition-colors border border-zinc-800"
              >
                Cancel
              </button>
              <button 
                onClick={startBot}
                className="flex-2 px-6 py-2 rounded-lg bg-blue-600 text-white text-[10px] font-bold uppercase tracking-widest hover:bg-blue-500 transition-all shadow-lg shadow-blue-600/10"
              >
                Start Automation
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Free trial active banner */}
      {subAccess.isTrial && subscription && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
          <div className="bg-amber-500/10 border border-amber-500/25 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="size-10 bg-amber-500/20 rounded-full flex items-center justify-center text-amber-400">
                <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h4 className="text-white font-bold">Free Trial Active</h4>
                <p className="text-sm text-amber-200/80">
                  24-hour trial · Up to {usageLimit} applications · 1 LinkedIn account · Expires{" "}
                  {formatPeriodEnd(subscription.current_period_end)}
                </p>
              </div>
            </div>
            <Link
              href="/pricing"
              className="px-6 py-2.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-white font-bold rounded-xl transition-all shrink-0 text-sm"
            >
              Upgrade Anytime
            </Link>
          </div>
        </div>
      )}

      {/* Upgrade banner — when no active trial or paid plan */}
      {subscriptionKnown && !subAccess.canApply && !subAccess.isTrial && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
          <div className="bg-indigo-600/20 border border-indigo-500/30 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="size-10 bg-indigo-500/20 rounded-full flex items-center justify-center text-indigo-400">
                <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h4 className="text-white font-bold">
                  {subAccess.isExpiredTrial
                    ? "Trial Expired"
                    : subscription?.plan === "free" || !subscription?.plan
                      ? "Start Your Free Trial"
                      : "Reactivate Your Plan"}
                </h4>
                <p className="text-sm text-indigo-200/80">
                  {subAccess.isExpiredTrial
                    ? "Your 24-hour free trial has ended. Upgrade to keep applying automatically."
                    : subscription?.plan === "free" || !subscription?.plan
                      ? "Try LinkdApply free for 24 hours — 10 applications, no credit card required."
                      : "You need an active subscription to launch the bot and automate your applications."}
                </p>
              </div>
            </div>
            <Link
              href={
                subscription?.plan === "free" || subAccess.isExpiredTrial || !subscription?.plan
                  ? "/pricing?trial=1"
                  : "/pricing"
              }
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-all shadow-lg shrink-0"
            >
              {subscription?.plan === "free" || subAccess.isExpiredTrial || !subscription?.plan
                ? "Start Free Trial"
                : "View Plans"}
            </Link>
          </div>
        </div>
      )}

      {/* Home: status, activity, primary actions */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-4">
        <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-sm">
          <div className="flex flex-col lg:flex-row lg:items-start gap-6">
            <div className="flex items-start gap-4 flex-1 min-w-0">
              <div
                className={`size-12 shrink-0 rounded-xl flex items-center justify-center ${
                  isStarting
                    ? "bg-amber-500/15 text-amber-400"
                    : botStatus === "running"
                      ? "bg-blue-600/15 text-blue-400"
                      : botStatus === "error"
                        ? "bg-red-600/15 text-red-400"
                        : "bg-zinc-900 text-zinc-500"
                }`}
              >
                {isStarting ? (
                  <svg className="size-6 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path
                      className="opacity-90"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                ) : botStatus === "running" ? (
                  <svg className="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  </svg>
                ) : (
                  <svg className="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </div>
              <div className="min-w-0 flex-1 space-y-3">
                <div>
                  <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Bot</p>
                  <p className="text-xl font-semibold text-white tracking-tight">
                    {isStarting
                      ? "Connecting…"
                      : botStatus === "running"
                        ? "Running"
                        : botStatus === "error"
                          ? "Backend unreachable"
                          : "Stopped"}
                  </p>
                  <p className="text-xs text-zinc-500 mt-1">
                    {isStarting
                      ? "Starting supervisor and workers…"
                      : botStatus === "running"
                        ? "Automation is active."
                        : "Start when you are ready to apply."}
                  </p>
                </div>
                <div className="grid sm:grid-cols-2 gap-3 text-xs">
                  <div className="rounded-lg bg-zinc-900/60 border border-zinc-800/80 px-3 py-2">
                    <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Last apply</p>
                    {lastApplied?.company || lastApplied?.job_title ? (
                      <>
                        <p className="text-zinc-200 font-medium truncate">{lastApplied.job_title || "—"}</p>
                        <p className="text-zinc-500 truncate">{lastApplied.company}</p>
                        <p className="text-[10px] text-zinc-600 mt-0.5">{formatShortTime(lastApplied.timestamp)}</p>
                      </>
                    ) : (
                      <p className="text-zinc-600">No applications yet</p>
                    )}
                  </div>
                  <div className="rounded-lg bg-zinc-900/60 border border-zinc-800/80 px-3 py-2">
                    <p className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Last error</p>
                    {lastFailed?.company || lastFailed?.job_title || lastFailed?.reason ? (
                      <>
                        <p className="text-zinc-200 font-medium truncate">{lastFailed.job_title || "—"}</p>
                        <p className="text-zinc-500 truncate">{lastFailed.company}</p>
                        {lastFailed.reason ? (
                          <p className="text-[10px] text-red-400/90 mt-1 line-clamp-2">{lastFailed.reason}</p>
                        ) : null}
                        <p className="text-[10px] text-zinc-600 mt-0.5">{formatShortTime(lastFailed.timestamp)}</p>
                      </>
                    ) : (
                      <p className="text-zinc-600">No failures recorded</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row lg:flex-col gap-4 lg:items-end lg:min-w-[200px] shrink-0">
              <div className="rounded-lg bg-zinc-900/50 border border-zinc-900 px-4 py-3 w-full sm:w-auto">
                <div className="text-lg font-bold text-white tracking-tight">
                  {stats?.monthly_count ?? 0}
                  <span className="text-zinc-600 text-xs font-medium ml-1">
                    / {applyLimit || usageLimit || "?"}
                  </span>
                </div>
                <div className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Monthly quota</div>
                <div className="mt-2 w-full sm:w-36 h-1 bg-zinc-900 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-1000"
                    style={{
                      width: `${Math.min(
                        100,
                        applyLimit > 0 ? ((stats?.monthly_count ?? 0) / applyLimit) * 100 : 0
                      )}%`,
                    }}
                  />
                </div>
              </div>

              <div className="flex flex-wrap gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    if (!subActive) {
                      window.location.href =
                        subscription?.plan === "free" || subAccess.isExpiredTrial
                          ? "/pricing?trial=1"
                          : "/pricing";
                      return;
                    }
                    setShowConfirm(true);
                  }}
                  disabled={startDisabled && subActive}
                  title={
                    !isBackendHealthy
                      ? "Backend offline"
                      : !subActive
                        ? subAccess.isExpiredTrial
                          ? "Trial expired — upgrade to continue"
                          : "Start a free trial or subscribe to apply"
                        : undefined
                  }
                  className={`px-4 py-2.5 rounded-lg text-xs font-bold uppercase tracking-widest transition-all ${
                    startDisabled ? "opacity-40 cursor-not-allowed" : ""
                  } ${
                    subActive ? "bg-blue-600 text-white hover:bg-blue-500" : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                  }`}
                >
                  Start
                </button>
                <button
                  type="button"
                  onClick={stopBot}
                  disabled={stopDisabled}
                  title={botStatus !== "running" ? "Bot is not running" : undefined}
                  className="px-4 py-2.5 rounded-lg bg-red-600 text-white text-xs font-bold uppercase tracking-widest hover:bg-red-500 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {isStopping ? "Stopping…" : "Stop"}
                </button>
                <button
                  type="button"
                  onClick={openLogsModal}
                  disabled={logsDisabled}
                  className="px-4 py-2.5 rounded-lg border border-zinc-700 bg-zinc-900 text-zinc-200 text-xs font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Logs
                </button>
                <button
                  type="button"
                  onClick={goToSettings}
                  className="px-4 py-2.5 rounded-lg border border-zinc-700 bg-zinc-900 text-zinc-200 text-xs font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all"
                >
                  Settings
                </button>
              </div>
            </div>
          </div>

          {connectionError && (
            <div className="mt-5 rounded-lg border border-red-500/25 bg-red-950/40 px-4 py-3 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
              <div className="min-w-0">
                <p className="text-[10px] font-bold text-red-400 uppercase tracking-wider mb-1">Could not complete action</p>
                <p className="text-sm text-red-200/95 break-words">{connectionError}</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setConnectionError(null);
                  openLogsModal();
                }}
                className="shrink-0 px-3 py-1.5 rounded-md bg-red-600/30 text-red-100 text-[10px] font-bold uppercase tracking-wider hover:bg-red-600/50 border border-red-500/30"
              >
                View logs
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Logs modal */}
      {showLogsModal && (
        <div className="fixed inset-0 z-[220] flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 gap-3 flex-wrap">
              <div className="flex items-center gap-3 min-w-0">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest shrink-0">
                  Bot logs
                </h3>
                {botRuns.length > 0 && (
                  <select
                    value={selectedLogRunId}
                    onChange={(e) => {
                      const val = e.target.value;
                      const runId = val === "" ? "" : Number(val);
                      setSelectedLogRunId(runId);
                      loadBotLogs(runId);
                    }}
                    className="max-w-[220px] bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-[10px] text-zinc-300 focus:outline-none focus:border-blue-600"
                  >
                    {botRuns.map((run) => (
                      <option key={run.id} value={run.id}>
                        Run #{run.id}
                        {run.start_time
                          ? ` · ${formatShortTime(run.start_time)}`
                          : ""}
                        {run.status ? ` · ${run.status}` : ""}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  disabled={logsLoading}
                  onClick={() => loadBotLogs(selectedLogRunId)}
                  className="px-2.5 py-1 rounded-lg border border-zinc-800 text-zinc-400 text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-900 disabled:opacity-40"
                >
                  Refresh
                </button>
                <button
                  type="button"
                  disabled={logsLoading || !logsPayload?.logs}
                  onClick={async () => {
                    const text = logsPayload?.logs || "";
                    try {
                      await navigator.clipboard.writeText(text);
                    } catch {
                      // Clipboard API can be unavailable (http / older browsers)
                      const ta = document.createElement("textarea");
                      ta.value = text;
                      document.body.appendChild(ta);
                      ta.select();
                      document.execCommand("copy");
                      document.body.removeChild(ta);
                    }
                    setLogsCopied(true);
                    setTimeout(() => setLogsCopied(false), 2000);
                  }}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[10px] font-bold uppercase tracking-widest transition-colors disabled:opacity-40 ${
                    logsCopied
                      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                      : "border-zinc-800 text-zinc-400 hover:bg-zinc-900 hover:text-white"
                  }`}
                >
                  {logsCopied ? (
                    <>
                      <svg className="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Copied
                    </>
                  ) : (
                    <>
                      <svg className="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copy
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowLogsModal(false)}
                  className="text-zinc-500 hover:text-white p-1 rounded"
                  aria-label="Close"
                >
                  <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4 text-xs font-mono text-zinc-300 space-y-4">
              {logsLoading && <p className="text-zinc-500">Loading…</p>}
              {!logsLoading && logsPayload?.infra && logsPayload.infra.length > 0 && (
                <div className="space-y-3">
                  {logsPayload.infra.map((block) => (
                    <div key={block.filename}>
                      <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">{block.title}</p>
                      <pre className="whitespace-pre-wrap break-words bg-black/40 rounded-lg p-3 border border-zinc-800/80 text-[11px] leading-relaxed">
                        {block.content || "(empty)"}
                      </pre>
                    </div>
                  ))}
                </div>
              )}
              {!logsLoading && logsPayload?.profiles && logsPayload.profiles.length > 0 && (
                <div className="space-y-3">
                  {logsPayload.profiles.map((block) => (
                    <div key={block.filename}>
                      <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">
                        Profile {block.id}
                      </p>
                      <pre className="whitespace-pre-wrap break-words bg-black/40 rounded-lg p-3 border border-zinc-800/80 text-[11px] leading-relaxed">
                        {block.content || "(empty)"}
                      </pre>
                    </div>
                  ))}
                </div>
              )}
              {!logsLoading && logsPayload && !logsPayload.infra?.length && !logsPayload.profiles?.length && (
                <pre className="whitespace-pre-wrap break-words text-zinc-400">{logsPayload.logs}</pre>
              )}
            </div>
            {!logsLoading && logsPayload?.log_dir && (
              <div className="px-4 py-2 border-t border-zinc-800 text-[10px] text-zinc-500 font-mono">
                {logsPayload.run_id != null && (
                  <span className="text-zinc-600 uppercase tracking-wider font-bold mr-2">
                    Run #{logsPayload.run_id}
                  </span>
                )}
                <span className="text-zinc-600 uppercase tracking-wider font-bold mr-2">Log dir</span>
                {logsPayload.log_dir}
                {logsPayload.files && logsPayload.files.length > 0 && (
                  <span className="ml-2">({logsPayload.files.map((f) => f.filename).join(", ")})</span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        
        {/* Toast Notification - Minimal */}
        {message && (
          <div className="fixed bottom-6 right-6 z-[100] animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className={`pl-4 pr-2 py-2 rounded-lg flex items-center gap-4 shadow-2xl border backdrop-blur-xl ${
              message.type === 'success' ? 'bg-zinc-950/90 border-emerald-500/20 text-emerald-400' : 
              message.type === 'warning' ? 'bg-zinc-950/90 border-amber-500/20 text-amber-400' :
              'bg-zinc-950/90 border-red-500/20 text-red-400'
            }`}>
              <div className="flex items-center gap-3">
                <div className={`size-1.5 rounded-full animate-pulse ${
                   message.type === 'success' ? 'bg-emerald-500' : 
                   message.type === 'warning' ? 'bg-amber-500' : 'bg-red-500'
                }`}></div>
                <p className="text-[11px] font-medium text-zinc-300 pr-2 border-r border-zinc-800">{message.text}</p>
                <button onClick={() => setMessage(null)} className="size-6 rounded flex items-center justify-center hover:bg-zinc-900 transition-colors">
                  <svg className="size-3 opacity-40 hover:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Layout Grid */}
        <div className="grid lg:grid-cols-12 gap-8">
          
          {/* Left Sidebar - Minimal */}
          <aside id="dashboard-configuration" className="lg:col-span-3 space-y-4 scroll-mt-24">
            <div className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden shadow-sm">
              <div className="px-4 py-2.5 bg-zinc-900/50 border-b border-zinc-900">
                <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Configuration</h3>
              </div>
              <nav className="p-1 space-y-0.5">
                {CONFIG_FILES.map((file) => (
                  <button
                    key={file}
                    onClick={() => setActiveTab(file)}
                    className={`w-full flex items-center px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                      activeTab === file
                        ? "bg-blue-600 text-white font-bold"
                        : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900"
                    }`}
                  >
                    <span className="capitalize">{file.split('.')[0]}</span>
                  </button>
                ))}
              </nav>
            </div>

            <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-4 shadow-sm">
              <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-3">Settings</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-[10px] font-medium text-zinc-500 uppercase">Bot Speed</span>
                    <span className="text-[10px] font-bold text-blue-500">{botSpeed}x</span>
                  </div>
                  <input 
                    type="range" 
                    min="1" 
                    max="10" 
                    value={botSpeed} 
                    onChange={(e) => updateBotSpeed(parseInt(e.target.value))}
                    className="w-full h-1 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                </div>
              </div>
            </div>

            <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-4 shadow-sm">
              <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-3">Resume</h3>
              <div className="relative group">
                <input type="file" accept=".pdf" onChange={handleResumeUpload} className="absolute inset-0 size-full opacity-0 cursor-pointer z-10" disabled={isUploading} />
                <div className={`rounded-lg border border-dashed p-3 text-center transition-all ${isUploading ? 'bg-blue-600/5 border-blue-600/30' : 'border-zinc-800 hover:border-zinc-700'}`}>
                  <p className="text-[10px] text-zinc-500 truncate mb-1">{resumeName || "No file"}</p>
                  <span className="text-[9px] font-bold text-blue-500 uppercase tracking-widest">Update</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => signOut({ callbackUrl: "/", redirect: true })}
              className="w-full py-2 text-[10px] font-bold text-zinc-600 uppercase tracking-widest hover:text-red-500 transition-colors"
            >
              Sign Out
            </button>
          </aside>

          {/* Main Editor Area - Minimal */}
          <section className="lg:col-span-9 flex flex-col h-[650px]">
            <div className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden shadow-sm flex flex-col h-full">
              <div className="flex justify-between items-center px-4 py-2 border-b border-zinc-900 bg-zinc-900/30">
                <div className="flex items-center gap-4">
                  <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                    Editor: <span className="text-blue-500 font-mono ml-1 lowercase">{activeTab}</span>
                  </h2>
                  <div className="flex bg-zinc-900 rounded p-0.5">
                    <button onClick={() => setIsFormMode(true)} className={`px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded transition-all ${isFormMode ? 'bg-zinc-800 text-white' : 'text-zinc-600 hover:text-zinc-400'}`}>Form</button>
                    <button onClick={() => setIsFormMode(false)} className={`px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded transition-all ${!isFormMode ? 'bg-zinc-800 text-white' : 'text-zinc-600 hover:text-zinc-400'}`}>Code</button>
                  </div>
                </div>
                <button onClick={saveConfig} disabled={isSaving || isLoading} className="px-3 py-1 bg-blue-600 text-white text-[10px] font-bold uppercase tracking-widest rounded hover:bg-blue-500 transition-all disabled:opacity-50">
                  {isSaving ? "Saving..." : "Save"}
                </button>
              </div>

              <div className="flex-1 relative p-6 overflow-hidden bg-black/20">
                {isFormMode ? (
                  <>
                    {activeTab === "personals.py" && <PersonalsForm data={formData} onChange={setFormData} />}
                    {activeTab === "search.py" && <SearchForm data={formData} onChange={setFormData} />}
                    {activeTab === "settings.py" && <SettingsForm data={formData} onChange={setFormData} />}
                    {activeTab === "questions.py" && <QuestionsForm data={formData} onChange={setFormData} />}
                    {activeTab === "secrets.py" && (
                      <SecretsForm data={formData} onChange={setFormData} />
                    )}
                  </>
                ) : (
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="w-full h-full bg-transparent text-zinc-300 font-mono text-xs leading-loose resize-none focus:outline-none"
                    spellCheck="false"
                  />
                )}
              </div>
            </div>
          </section>
        </div>

        {/* Application History - Minimal */}
        <div className="mt-12 bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden shadow-sm">
            <div className="px-4 py-3 bg-zinc-900/50 border-b border-zinc-900 flex items-center justify-between">
                <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                    Application History
                    <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                </h2>
                <div className="flex gap-4">
                   <div className="text-[9px] font-bold text-zinc-600 uppercase tracking-tight">
                       Applied: <span className="text-zinc-300">{stats?.applied || 0}</span>
                   </div>
                   <div className="text-[9px] font-bold text-zinc-600 uppercase tracking-tight">
                       Failed: <span className="text-zinc-300">{stats?.failed || 0}</span>
                   </div>
                </div>
            </div>
            
            <div className="overflow-x-auto max-h-[400px] scrollbar-thin scrollbar-thumb-zinc-900">
                <table className="w-full text-left">
                  <thead className="sticky top-0 bg-zinc-950 z-10">
                    <tr className="border-b border-zinc-900">
                      <th className="px-4 py-3 text-[9px] font-bold text-zinc-500 uppercase tracking-wider">Company</th>
                      <th className="px-4 py-3 text-[9px] font-bold text-zinc-500 uppercase tracking-wider">Role</th>
                      <th className="px-4 py-3 text-[9px] font-bold text-zinc-500 uppercase tracking-wider text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900">
                    {history.length > 0 ? history.map((app, idx) => (
                      <tr key={idx} className="hover:bg-zinc-900/20 transition-colors">
                        <td className="px-4 py-3">
                          <p className="text-xs font-semibold text-zinc-300">{app.company}</p>
                          <p className="text-[9px] text-zinc-600 uppercase tracking-tighter">
                            {app.timestamp
                              ? new Date(app.timestamp).toLocaleString(undefined, {
                                  dateStyle: "short",
                                  timeStyle: "short",
                                })
                              : ""}
                          </p>
                        </td>
                        <td className="px-4 py-3 text-xs text-zinc-500">{app.job_title}</td>
                        <td className="px-4 py-3 text-right">
                          <span className={`inline-flex px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-tight ${
                            app.status === 'applied' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'
                          }`}>
                            {app.status}
                          </span>
                        </td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan={3} className="px-4 py-10 text-center text-zinc-600 text-[10px] uppercase tracking-widest">
                          No recent activity
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
            </div>
        </div>
      </div>
    </div>
  );
}
