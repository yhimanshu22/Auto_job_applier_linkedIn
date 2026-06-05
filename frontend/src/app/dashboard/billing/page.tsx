"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";

type Subscription = {
  plan?: string;
  status?: string;
  current_period_end?: number | string | null;
  billing_cycle?: string;
  limit?: number;
};

type Stats = {
  monthly_count?: number;
  total?: number;
};

type ActiveBots = {
  active: number;
  supervisor: number;
  automation_tasks: number;
  limit: number;
};

// Static price + limit lookup. Kept in sync with backend `PRICE_MAP` and
// `plan_limits.py` — adding a new plan means adding a row here.
const PLAN_META: Record<
  string,
  { label: string; price: string; accountsLimit: number; botsLimit: number }
> = {
  free_trial: { label: "Free Trial", price: "$0", accountsLimit: 1, botsLimit: 1 },
  free: { label: "Free", price: "$0", accountsLimit: 1, botsLimit: 1 },
  starter: { label: "Starter", price: "$19", accountsLimit: 1, botsLimit: 1 },
  pro: { label: "Pro", price: "$49", accountsLimit: 3, botsLimit: 2 },
  agency: { label: "Agency", price: "$149", accountsLimit: 10, botsLimit: 5 },
};

const FALLBACK_PLAN_META = {
  label: "Free Trial",
  price: "$0",
  accountsLimit: 1,
  botsLimit: 1,
};

function fmtPeriodEnd(value: number | string | null | undefined): string {
  if (value === null || value === undefined) return "—";
  try {
    if (typeof value === "number") {
      return new Date(value * 1000).toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
    }
    return new Date(value).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return String(value);
  }
}

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

export default function BillingPage() {
  const { data: session, status } = useSession();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [accountsCount, setAccountsCount] = useState<number | null>(null);
  const [activeBots, setActiveBots] = useState<ActiveBots | null>(null);
  const [isBackendHealthy, setIsBackendHealthy] = useState(true);
  const [loaded, setLoaded] = useState(false);

  const userId = session?.user?.email || "local-user";

  // Note: We don't bounce on ``status === "unauthenticated"``. Local installs
  // may run without a NextAuth session cookie; other dashboard pages fall back
  // to ``userId = "local-user"``.
  useEffect(() => {
    if (status === "loading") return;
    let cancelled = false;

    const load = async () => {
      try {
        const [subRes, statsRes, accountsRes, activeRes] = await Promise.all([
          fetch(
            `http://127.0.0.1:8000/api/billing/subscription?user_id=${encodeURIComponent(userId)}`
          ),
          fetch(
            `http://127.0.0.1:8000/api/applications/stats?user_id=${encodeURIComponent(userId)}`
          ),
          // Reuse the automation endpoint so the LinkedIn Accounts tile
          // shows the real DB-backed count instead of a hardcoded 1.
          fetch(`http://127.0.0.1:8000/api/linkedin-automation/accounts`),
          // Live concurrency for the Active Bots tile (supervisor +
          // automation task subprocesses for this user).
          fetch(
            `http://127.0.0.1:8000/api/bot/active?user_id=${encodeURIComponent(userId)}`
          ),
        ]);
        if (cancelled) return;
        if (subRes.ok) setSubscription(await subRes.json());
        if (statsRes.ok) setStats(await statsRes.json());
        if (accountsRes.ok) {
          const j = await accountsRes.json();
          setAccountsCount(Array.isArray(j?.accounts) ? j.accounts.length : 0);
        }
        if (activeRes.ok) setActiveBots(await activeRes.json());
        setIsBackendHealthy(subRes.ok || statsRes.ok);
      } catch {
        if (!cancelled) setIsBackendHealthy(false);
      } finally {
        if (!cancelled) setLoaded(true);
      }
    };

    load();
    // Cheap re-poll just for the live concurrency counter. Subscription /
    // stats / accounts barely move so we don't refetch them here.
    const interval = window.setInterval(async () => {
      try {
        const res = await fetch(
          `http://127.0.0.1:8000/api/bot/active?user_id=${encodeURIComponent(userId)}`
        );
        if (!cancelled && res.ok) setActiveBots(await res.json());
      } catch {
        /* leave previous value in place on a transient failure */
      }
    }, 10_000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [status, userId]);

  const handleManageBilling = async () => {
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/billing/create-portal-session`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId }),
        }
      );
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        alert(data.detail || "Failed to open billing portal.");
      }
    } catch {
      alert("Failed to open billing portal");
    }
  };

  const planKey = (subscription?.plan || "free_trial").toLowerCase();
  const meta = PLAN_META[planKey] ?? FALLBACK_PLAN_META;
  const usageLimit = subscription?.limit ?? 10;
  const monthly = stats?.monthly_count ?? 0;
  const usagePct =
    usageLimit > 0 ? Math.min(100, (monthly / usageLimit) * 100) : 0;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-400 font-sans selection:bg-blue-600/20">
      {/* Slim navigation — mirrors /dashboard exactly. */}
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
                className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest hover:text-white transition-colors"
              >
                Automation
              </Link>
              <Link
                href="/dashboard/billing"
                className="text-[10px] font-bold text-white uppercase tracking-widest"
              >
                Billing
              </Link>
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800">
                <div
                  className={`size-1.5 rounded-full ${isBackendHealthy ? "bg-emerald-500" : "bg-red-500"}`}
                />
                <span className="text-[10px] font-medium text-zinc-400 uppercase tracking-tighter">
                  System {isBackendHealthy ? "OK" : "Error"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Page header */}
        <div className="mb-6">
          <h1 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">
            Billing &amp; Subscription
          </h1>
          <p className="text-xs text-zinc-600">
            Manage your plan, view usage, and update payment methods.
          </p>
        </div>

        {/* Top row — plan summary + price */}
        <div className="grid lg:grid-cols-12 gap-6">
          <section className="lg:col-span-8">
            <div className="bg-zinc-950 border border-zinc-900 rounded-xl shadow-sm overflow-hidden">
              <div className="px-4 py-3 bg-zinc-900/50 border-b border-zinc-900 flex items-center justify-between">
                <h2 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                  Current Plan
                </h2>
                {subscription?.status && (
                  <span className="text-[9px] font-bold text-emerald-400 uppercase tracking-widest">
                    {subscription.status}
                  </span>
                )}
              </div>
              <div className="p-5 grid sm:grid-cols-2 gap-6">
                <div>
                  <p className="text-2xl font-semibold text-white tracking-tight">
                    {meta.label}
                  </p>
                  <p className="text-[10px] text-zinc-600 mt-1 uppercase tracking-widest font-bold">
                    {subscription?.billing_cycle || "—"}
                  </p>
                  <p className="text-[11px] text-zinc-500 mt-3">
                    Next billing:{" "}
                    <span className="text-zinc-300">
                      {fmtPeriodEnd(subscription?.current_period_end)}
                    </span>
                  </p>
                </div>
                <div className="sm:text-right">
                  <p className="text-3xl font-semibold text-white tracking-tight">
                    {meta.price}
                    <span className="text-zinc-600 text-sm font-medium ml-1">
                      /mo
                    </span>
                  </p>
                  <div className="mt-4 flex sm:justify-end gap-2">
                    <button
                      type="button"
                      onClick={handleManageBilling}
                      className="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold uppercase tracking-widest transition-colors"
                    >
                      Manage
                    </button>
                    <Link
                      href="/pricing"
                      className="px-3 py-1.5 rounded bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-300 text-[10px] font-bold uppercase tracking-widest transition-colors"
                    >
                      Change Plan
                    </Link>
                  </div>
                </div>
              </div>
              {/* Monthly usage row */}
              <div className="px-5 py-4 border-t border-zinc-900">
                <div className="flex items-end justify-between mb-2">
                  <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                    Monthly Applications
                  </span>
                  <span className="text-[10px] text-zinc-400 font-mono">
                    {monthly} / {usageLimit}
                  </span>
                </div>
                <div className="h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-700"
                    style={{ width: `${usagePct}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Trial banner (only when applicable) — sits below the plan card */}
            {subscription?.plan === "free_trial" && (
              <div className="mt-4 bg-zinc-950 border border-amber-500/20 rounded-xl p-3 text-[11px] text-zinc-400 leading-relaxed">
                <span className="text-amber-400 font-bold uppercase tracking-widest text-[10px]">
                  Trial —
                </span>{" "}
                expires on{" "}
                <span className="text-zinc-200">
                  {fmtPeriodEnd(subscription.current_period_end)}
                </span>
                . Upgrade to keep automation running.
              </div>
            )}
          </section>

          {/* Right column — limits */}
          <section className="lg:col-span-4 grid gap-6">
            <LimitTile
              label="LinkedIn Accounts"
              value={accountsCount ?? 0}
              limit={meta.accountsLimit}
              loaded={loaded}
            />
            <LimitTile
              label="Active Bots"
              value={activeBots?.active ?? 0}
              limit={activeBots?.limit ?? meta.botsLimit}
              loaded={loaded}
              hint={
                activeBots
                  ? `${activeBots.supervisor} supervisor + ${activeBots.automation_tasks} automation task(s) running now. Plan cap: ${activeBots.limit}.`
                  : "Concurrently running now / plan limit."
              }
            />
          </section>
        </div>
      </main>
    </div>
  );
}

function LimitTile({
  label,
  value,
  limit,
  loaded,
  hint,
}: {
  label: string;
  value: number;
  limit: number;
  loaded: boolean;
  hint?: string;
}) {
  const pct = limit > 0 ? Math.min(100, (value / limit) * 100) : 0;
  return (
    <div className="bg-zinc-950 border border-zinc-900 rounded-xl shadow-sm overflow-hidden">
      <div className="px-4 py-3 bg-zinc-900/50 border-b border-zinc-900">
        <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
          {label}
        </h3>
      </div>
      <div className="p-4">
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-white tracking-tight">
            {loaded ? value : "—"}
          </span>
          <span className="text-xs text-zinc-600">/ {limit}</span>
        </div>
        <div className="mt-3 h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden">
          <div
            className="h-full bg-zinc-500 transition-all duration-700"
            style={{ width: `${pct}%` }}
          />
        </div>
        {hint && <p className="text-[10px] text-zinc-600 mt-3">{hint}</p>}
      </div>
    </div>
  );
}
