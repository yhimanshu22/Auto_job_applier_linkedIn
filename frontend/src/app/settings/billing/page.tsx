"use client";

import React, { useState } from "react";
import { useSession } from "next-auth/react";

export default function BillingSettingsPage() {
  const [loading, setLoading] = useState(false);
  const { data: session } = useSession();
  const userId = session?.user?.email;

  async function openBillingPortal() {
    if (!userId) {
      alert("Sign in to manage billing.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/billing/create-portal-session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          user_id: userId,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed to open portal");
      }

      window.location.href = data.url;
    } catch (error) {
      console.error(error);
      alert("Failed to open billing portal. Ensure backend is running and customer ID is valid.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-white text-zinc-900 py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[800px] hero-gradient opacity-10 pointer-events-none"></div>

      <div className="max-w-3xl mx-auto relative z-10">
        <h1 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900 mb-12">
          Billing & Subscription
        </h1>

        <div className="bg-zinc-50/50 rounded-3xl shadow-xl border border-zinc-100 overflow-hidden backdrop-blur-sm hover:bg-white hover:border-accent/20 transition-all">
          <div className="px-8 py-10 sm:p-12">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-8">
              <div className="space-y-4 max-w-xl">
                <h3 className="text-2xl font-bold text-zinc-900">Manage your plan</h3>
                <p className="text-zinc-500 leading-relaxed">
                  Update your payment method, view your billing history, or change your subscription plan safely via our secure Stripe portal.
                </p>
              </div>
              <div className="shrink-0">
                <button
                  type="button"
                  onClick={openBillingPortal}
                  disabled={loading || !userId}
                  className="purple-gradient-button inline-flex items-center px-8 py-4 rounded-xl text-white font-semibold transition-all hover:scale-[1.02] disabled:opacity-50 shadow-lg"
                >
                  {loading ? "Opening Portal..." : "Manage Billing"}
                </button>
              </div>
            </div>

            <div className="mt-12 pt-8 border-t border-zinc-100">
               <div className="flex items-center gap-3 text-sm text-zinc-400 font-medium tracking-wide uppercase">
                  <div className="size-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]"></div>
                  Security powered by Stripe
               </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
