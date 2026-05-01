"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

export default function BillingPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [subscription, setSubscription] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const userId = session?.user?.email || "local-user";

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
      return;
    }

    const fetchData = async () => {
      try {
        const [subRes, statsRes] = await Promise.all([
          fetch(`http://127.0.0.1:8000/api/billing/subscription?user_id=${userId}`),
          fetch(`http://127.0.0.1:8000/api/applications/stats?user_id=${userId}`)
        ]);

        if (subRes.ok) setSubscription(await subRes.json());
        if (statsRes.ok) setStats(await statsRes.json());
      } catch (err) {
        console.error("Failed to fetch billing data");
      } finally {
        setIsLoading(false);
      }
    };

    if (status === "authenticated") {
        fetchData();
    }
  }, [status, userId, router]);

  const handleManageBilling = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/billing/create-portal-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId })
      });
      const data = await res.json();
      if (data.url) window.location.href = data.url;
    } catch (err) {
      alert("Failed to open billing portal");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0f172a] flex items-center justify-center">
        <div className="size-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f172a] text-zinc-200">
       {/* Top Navbar */}
       <nav className="border-b border-zinc-800/50 bg-[#0f172a]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/dashboard" className="flex items-center group">
              <svg className="size-5 text-zinc-500 group-hover:text-white transition-colors mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span className="font-serif text-lg font-semibold text-white">Back to Dashboard</span>
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-4 py-12">
        <div className="mb-12">
            <h1 className="text-4xl font-serif font-medium text-white mb-2">Billing & Subscription</h1>
            <p className="text-zinc-400">Manage your plan, view usage, and update payment methods.</p>
        </div>

        <div className="grid gap-8">
            {/* Plan Status Card */}
            <div className="bg-[#1e293b] border border-zinc-800 rounded-3xl p-8 shadow-xl">
                <div className="flex justify-between items-start mb-8">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <span className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Current Plan</span>
                            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                                subscription?.plan === 'pro' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' :
                                subscription?.plan === 'agency' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                                'bg-zinc-800 text-zinc-400 border-zinc-700'
                            }`}>
                                {subscription?.plan || 'Free Trial'}
                            </span>
                        </div>
                        <h2 className="text-3xl font-bold text-white capitalize">{subscription?.plan || 'Free Trial'} Plan</h2>
                    </div>
                    <div className="text-right">
                        <div className="text-2xl font-bold text-white">
                            {subscription?.plan === 'free_trial' ? '$0' : 
                             subscription?.plan === 'starter' ? '$19' :
                             subscription?.plan === 'pro' ? '$49' : '$149'}
                            <span className="text-zinc-500 text-sm font-medium">/mo</span>
                        </div>
                        <p className="text-xs text-zinc-500 font-medium">Next billing: {subscription?.current_period_end ? new Date(subscription.current_period_end * 1000).toLocaleDateString() : 'N/A'}</p>
                    </div>
                </div>

                <div className="space-y-6">
                    <div>
                        <div className="flex justify-between items-end mb-2">
                            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Monthly Usage</h3>
                            <span className="text-sm text-zinc-400 font-medium">{stats?.monthly_count || 0} / {subscription?.limit || 10} applications</span>
                        </div>
                        <div className="h-2 w-full bg-zinc-900 rounded-full overflow-hidden">
                            <div 
                                className="h-full bg-blue-500 transition-all duration-1000 shadow-[0_0_8px_rgba(59,130,246,0.5)]" 
                                style={{ width: `${Math.min(100, (subscription?.limit > 0) ? (stats?.monthly_count / subscription.limit) * 100 : 0)}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="flex gap-4 pt-4 border-t border-zinc-800">
                        <button 
                            onClick={handleManageBilling}
                            className="flex-1 px-6 py-3 rounded-xl bg-white text-zinc-950 font-bold hover:bg-zinc-200 transition-all shadow-lg"
                        >
                            Manage Subscription
                        </button>
                        <Link 
                            href="/pricing"
                            className="flex-1 px-6 py-3 rounded-xl bg-zinc-800 text-white font-bold text-center hover:bg-zinc-700 transition-all border border-zinc-700"
                        >
                            Change Plan
                        </Link>
                    </div>
                </div>
            </div>

            {/* Account Limits Card */}
            <div className="grid sm:grid-cols-2 gap-6">
                <div className="bg-[#1e293b] border border-zinc-800 rounded-2xl p-6">
                    <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-4">LinkedIn Accounts</h3>
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-bold text-white">1</span>
                        <span className="text-zinc-500 text-sm">/ {subscription?.plan === 'pro' ? '3' : subscription?.plan === 'agency' ? '10' : '1'} limit</span>
                    </div>
                </div>
                <div className="bg-[#1e293b] border border-zinc-800 rounded-2xl p-6">
                    <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-4">Active Bots</h3>
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-bold text-white">1</span>
                        <span className="text-zinc-500 text-sm">/ {subscription?.plan === 'pro' ? '2' : subscription?.plan === 'agency' ? '5' : '1'} limit</span>
                    </div>
                </div>
            </div>

            {/* Trial Info */}
            {subscription?.plan === 'free_trial' && (
                <div className="bg-blue-600/10 border border-blue-500/20 rounded-2xl p-6">
                    <div className="flex gap-4">
                        <div className="size-10 bg-blue-500/20 rounded-full flex items-center justify-center text-blue-400 shrink-0">
                            <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <div>
                            <h4 className="text-white font-bold mb-1">Trial expires soon</h4>
                            <p className="text-sm text-zinc-400 leading-relaxed">
                                Your free trial will expire on {new Date(subscription.current_period_end * 1000).toLocaleString()}. 
                                Upgrade to a paid plan to keep applying and unlock advanced features like AI answers.
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
      </main>
    </div>
  );
}
