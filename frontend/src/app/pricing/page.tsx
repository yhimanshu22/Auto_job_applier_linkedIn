"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';

import PricingCard from '@/components/PricingCard';

type PlanType = "free_trial" | "starter" | "pro" | "agency";
type BillingCycle = "monthly" | "yearly";

const PLANS = [
  {
    key: "free_trial",
    title: "Free Trial",
    monthlyPrice: 0,
    yearlyMonthlyPrice: 0,
    yearlyTotal: 0,
    suffix: "1 day",
    badge: "No card required",
    description: "Try LinkdApply for 24 hours with limited applications.",
    features: [
      "1 LinkedIn account",
      "1 active bot",
      "10 applications total",
      "Basic dashboard access",
      "Application history preview",
      "Manual start/stop control",
      "Upgrade anytime",
    ],
  },
  {
    key: "starter",
    title: "Starter",
    monthlyPrice: 19,
    yearlyMonthlyPrice: 15,
    yearlyTotal: 180,
    description: "For individual job seekers who want consistent applications.",
    features: [
      "1 LinkedIn account",
      "1 active bot",
      "100 applications/month",
      "Basic dashboard",
      "Application history",
      "Job filters",
      "Safe daily limits",
      "Email support",
    ],
  },
  {
    key: "pro",
    title: "Pro",
    monthlyPrice: 49,
    yearlyMonthlyPrice: 39,
    yearlyTotal: 468,
    badge: "Most Popular",
    highlighted: true,
    description: "For serious job seekers who want AI answers and higher limits.",
    features: [
      "3 LinkedIn accounts",
      "2 active bots",
      "500 applications/month",
      "AI dynamic answers",
      "Resume-aware responses",
      "Advanced job filters",
      "Priority queue",
      "Export application history",
      "Priority support",
    ],
  },
  {
    key: "agency",
    title: "Agency",
    monthlyPrice: 149,
    yearlyMonthlyPrice: 119,
    yearlyTotal: 1428,
    description: "For agencies and power users managing multiple accounts.",
    features: [
      "10 LinkedIn accounts",
      "5 active bots",
      "3000 applications/month",
      "Team-ready usage",
      "Multi-account dashboard",
      "Advanced reporting",
      "Export reports",
      "Priority support",
      "Dedicated onboarding help",
    ],
  },
] as const;

import Header from '@/components/Header';
import Footer from '@/components/Footer';

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null);
  const [billingCycle, setBillingCycle] = useState<BillingCycle>("monthly");
  const { data: session } = useSession();
  const router = useRouter();

  async function startFreeTrial() {
    setLoading("free_trial");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/billing/start-free-trial", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          user_id: session?.user?.email || "local-user",
          email: session?.user?.email || "user@example.com"
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start trial");
      
      alert("Trial activated! Redirecting to dashboard...");
      router.push("/dashboard");
    } catch (error: any) {
      console.error(error);
      alert(error.message || "Failed to start free trial.");
    } finally {
      setLoading(null);
    }
  }

  async function startStripeCheckout(plan: Exclude<PlanType, "free_trial">) {
    setLoading(plan);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/billing/create-checkout-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan,
          billing_cycle: billingCycle,
          user_id: session?.user?.email || "local-user",
          email: session?.user?.email || "user@example.com",
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start checkout");
      window.location.href = data.url;
    } catch (error: any) {
      console.error(error);
      alert(error.message || "Failed to initiate checkout. Is the backend running?");
    } finally {
      setLoading(null);
    }
  }

  function handleBuy(plan: PlanType) {
    if (plan === "free_trial") {
      startFreeTrial();
      return;
    }
    startStripeCheckout(plan as Exclude<PlanType, "free_trial">);
  }

  return (
    <div className="flex flex-col min-h-screen bg-white selection:bg-accent/10">
      <Header />

      <main className="grow py-24 px-4 sm:px-6 lg:px-8 relative overflow-hidden flex flex-col items-center">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[800px] hero-gradient opacity-10 pointer-events-none"></div>
        
        <div className="max-w-7xl mx-auto relative z-10 w-full">
          <div className="text-center space-y-6 pt-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-[10px] font-bold uppercase tracking-widest text-accent">
              Start free. Upgrade when your job search scales.
            </div>
            <p className="font-serif text-[40px] lg:text-[64px] leading-[1.1] font-medium tracking-tight text-zinc-900">
              Choose your plan
            </p>
            <p className="text-zinc-500 max-w-2xl mx-auto text-lg">
              Try LinkdApply for 24 hours, then choose the plan that matches your application volume.
            </p>

            {/* Billing Cycle Toggle */}
            <div className="mt-8 inline-flex rounded-full border border-zinc-200 bg-zinc-50 p-1 shadow-sm">
              <button
                onClick={() => setBillingCycle("monthly")}
                className={`rounded-full px-8 py-2.5 text-sm font-bold transition-all ${
                  billingCycle === "monthly"
                    ? "bg-white text-zinc-950 shadow-sm"
                    : "text-zinc-500 hover:text-zinc-900"
                }`}
              >
                Monthly
              </button>

              <button
                onClick={() => setBillingCycle("yearly")}
                className={`rounded-full px-8 py-2.5 text-sm font-bold transition-all flex items-center gap-2 ${
                  billingCycle === "yearly"
                    ? "bg-white text-zinc-950 shadow-sm"
                    : "text-zinc-500 hover:text-zinc-900"
                }`}
              >
                Annual
                <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-bold text-green-700">
                  Save 20%
                </span>
              </button>
            </div>
          </div>

          <div className="mt-20 space-y-12 lg:space-y-0 lg:grid lg:grid-cols-4 lg:gap-x-4 items-stretch mb-24">
            {PLANS.map((plan) => (
              <PricingCard 
                key={plan.key}
                plan={plan}
                billingCycle={billingCycle}
                loading={loading === plan.key}
                onBuy={() => handleBuy(plan.key as PlanType)}
              />
            ))}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

