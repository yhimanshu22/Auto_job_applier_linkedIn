"use client";

import React, { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useSession } from 'next-auth/react';

import PricingCard from '@/components/PricingCard';
import { parseApiJson } from '@/lib/api-json';

type PlanType = "free_trial" | "starter" | "pro" | "agency";
type BillingCycle = "monthly" | "yearly";
type Currency = "inr" | "usd";

const PLANS = [
  {
    key: "free_trial",
    title: "Free Trial",
    monthlyPrice: 0,
    yearlyMonthlyPrice: 0,
    yearlyTotal: 0,
    inrMonthlyPrice: 0,
    inrYearlyMonthlyPrice: 0,
    inrYearlyTotal: 0,
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
    inrMonthlyPrice: 1599,
    inrYearlyMonthlyPrice: 1299,
    inrYearlyTotal: 15588,
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
    inrMonthlyPrice: 3999,
    inrYearlyMonthlyPrice: 3299,
    inrYearlyTotal: 39588,
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
    inrMonthlyPrice: 11999,
    inrYearlyMonthlyPrice: 9999,
    inrYearlyTotal: 119988,
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

const TRIAL_LOGIN_URL = `/login?callbackUrl=${encodeURIComponent("/pricing?trial=1")}`;
const PRICING_LOGIN_URL = `/login?callbackUrl=${encodeURIComponent("/pricing")}`;

function PricingPageContent() {
  const [loading, setLoading] = useState<string | null>(null);
  const [billingCycle, setBillingCycle] = useState<BillingCycle>("monthly");
  const [currency, setCurrency] = useState<Currency>("inr");
  const { data: session, status } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();
  const autoTrialStarted = useRef(false);

  const redirectToLogin = useCallback(
    (callbackUrl: string = TRIAL_LOGIN_URL) => {
      router.push(callbackUrl);
    },
    [router]
  );

  const startFreeTrial = useCallback(async () => {
    if (status === "loading") return;

    if (status !== "authenticated" || !session?.user?.email) {
      redirectToLogin();
      return;
    }

    const email = session.user.email;
    setLoading("free_trial");
    try {
      const res = await fetch("/api/billing/start-free-trial", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: email }),
      });

      const data = await parseApiJson<{ detail?: string; status?: string }>(res);
      if (res.status === 401 || res.status === 403) {
        redirectToLogin();
        return;
      }
      if (!res.ok) throw new Error(data.detail || "Failed to start trial");

      router.replace("/dashboard");
    } catch (error: unknown) {
      console.error(error);
      const message = error instanceof Error ? error.message : "Failed to start free trial.";
      alert(message);
    } finally {
      setLoading(null);
    }
  }, [redirectToLogin, router, session?.user?.email, status]);

  useEffect(() => {
    if (searchParams.get("trial") !== "1") return;
    if (status === "loading") return;

    if (status !== "authenticated" || !session?.user?.email) {
      redirectToLogin();
      return;
    }

    if (autoTrialStarted.current) return;
    autoTrialStarted.current = true;
    void startFreeTrial();
  }, [status, searchParams, startFreeTrial, session?.user?.email, redirectToLogin]);

  async function startPayUCheckout(plan: Exclude<PlanType, "free_trial">) {
    if (status === "loading") return;

    if (status !== "authenticated" || !session?.user?.email) {
      redirectToLogin(PRICING_LOGIN_URL);
      return;
    }

    const email = session.user.email;
    setLoading(plan);
    const qs = new URLSearchParams({
      plan,
      billing_cycle: billingCycle,
      user_id: email,
      email,
    });
    const name = session.user.name?.trim();
    if (name) qs.set("firstname", name);

    // PayU docs Step 1.3a: server-rendered HTML form auto-POSTs to PayU.
    window.location.href = `/api/billing/payu/checkout-page?${qs.toString()}`;
  }

  async function startStripeCheckout(plan: Exclude<PlanType, "free_trial">) {
    if (status === "loading") return;

    if (status !== "authenticated" || !session?.user?.email) {
      redirectToLogin(PRICING_LOGIN_URL);
      return;
    }

    const email = session.user.email;
    setLoading(plan);
    try {
      const res = await fetch("/api/billing/create-checkout-session", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan,
          billing_cycle: billingCycle,
          user_id: email,
          email,
        }),
      });

      const data = await parseApiJson<{ detail?: string; url?: string }>(res);
      if (res.status === 401 || res.status === 403) {
        redirectToLogin(PRICING_LOGIN_URL);
        return;
      }
      if (!res.ok) throw new Error(data.detail || "Failed to start checkout");
      if (!data.url) throw new Error("Checkout URL missing from server.");
      window.location.href = data.url;
    } catch (error: unknown) {
      console.error(error);
      const message = error instanceof Error ? error.message : "Failed to initiate checkout. Is the backend running?";
      alert(message);
    } finally {
      setLoading(null);
    }
  }

  function handleBuy(plan: PlanType) {
    if (status === "loading") return;

    if (plan === "free_trial") {
      if (status !== "authenticated" || !session?.user?.email) {
        redirectToLogin();
        return;
      }
      void startFreeTrial();
      return;
    }

    if (status !== "authenticated" || !session?.user?.email) {
      redirectToLogin(PRICING_LOGIN_URL);
      return;
    }
    if (currency === "inr") {
      void startPayUCheckout(plan as Exclude<PlanType, "free_trial">);
      return;
    }
    void startStripeCheckout(plan as Exclude<PlanType, "free_trial">);
  }

  return (
    <div className="flex flex-col min-h-screen bg-white selection:bg-accent/10">
      <Header />

      <main className="relative flex flex-col pt-32 pb-24 overflow-hidden min-h-screen">
        {/* Background Layers */}
        <div className="absolute top-0 left-0 w-full h-full grid-pattern pointer-events-none z-0 opacity-40"></div>
        <div className="absolute top-0 left-0 w-full h-full noise-texture pointer-events-none z-0"></div>
        <div className="absolute top-0 left-0 w-full h-[800px] natural-glow pointer-events-none z-0"></div>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[800px] hero-gradient opacity-15 pointer-events-none z-0"></div>
        
        <div className="relative z-10 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8">
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

            {/* Currency Toggle */}
            <div className="mt-8 flex justify-center">
              <div className="inline-flex rounded-full border border-zinc-200 bg-zinc-50 p-1 shadow-sm">
                <button
                  onClick={() => setCurrency("inr")}
                  className={`rounded-full px-6 py-2 text-sm font-bold transition-all ${
                    currency === "inr"
                      ? "bg-white text-zinc-950 shadow-sm"
                      : "text-zinc-500 hover:text-zinc-900"
                  }`}
                >
                  ₹ INR (India)
                </button>
                <button
                  onClick={() => setCurrency("usd")}
                  className={`rounded-full px-6 py-2 text-sm font-bold transition-all ${
                    currency === "usd"
                      ? "bg-white text-zinc-950 shadow-sm"
                      : "text-zinc-500 hover:text-zinc-900"
                  }`}
                >
                  $ USD (International)
                </button>
              </div>
            </div>

            {/* Billing Cycle Toggle */}
            <div className="mt-4 inline-flex rounded-full border border-zinc-200 bg-zinc-50 p-1 shadow-sm">
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

          <div className="mt-20 space-y-12 lg:space-y-0 lg:grid lg:grid-cols-4 lg:gap-x-4 items-stretch mb-12">
            {PLANS.map((plan) => (
              <PricingCard 
                key={plan.key}
                plan={plan}
                billingCycle={billingCycle}
                currency={currency}
                loading={loading === plan.key}
                onBuy={() => handleBuy(plan.key as PlanType)}
              />
            ))}
          </div>

          <p className="text-center text-sm text-zinc-500 max-w-3xl mx-auto mb-24">
            All prices for Indian customers are listed in Indian Rupees (INR) and are inclusive of applicable
            taxes. Indian payments are processed securely via PayU (UPI, cards, net banking). International
            payments are processed securely in USD via Stripe.
          </p>
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default function PricingPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-white">
          <div className="size-6 animate-spin rounded-full border-2 border-zinc-200 border-t-accent" />
        </div>
      }
    >
      <PricingPageContent />
    </Suspense>
  );
}

