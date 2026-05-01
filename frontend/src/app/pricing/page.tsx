"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

type PlanType = "free_trial" | "starter" | "pro" | "agency";

const PLANS = [
  {
    key: "free_trial",
    title: "Free Trial",
    price: 0,
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
    price: 19,
    suffix: "mo",
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
    price: 49,
    suffix: "mo",
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
    price: 149,
    suffix: "mo",
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

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null);
  const router = useRouter();

  async function startFreeTrial() {
    setLoading("free_trial");
    try {
      const res = await fetch("http://localhost:8000/api/billing/start-free-trial", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: "local-user" }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start trial");
      
      alert("Trial activated! Redirecting to dashboard...");
      router.push("/dashboard");
    } catch (error: any) {
      console.error(error);
      alert(error.message || "Failed to initiate trial. Is the backend running?");
    } finally {
      setLoading(null);
    }
  }

  async function startStripeCheckout(plan: PlanType) {
    setLoading(plan);
    try {
      const res = await fetch("http://localhost:8000/api/billing/create-checkout-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan,
          user_id: "local-user",
          email: "user@example.com",
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to start checkout");
      window.location.href = data.url;
    } catch (error) {
      console.error(error);
      alert("Failed to initiate checkout. Is the backend running?");
    } finally {
      setLoading(null);
    }
  }

  async function handleBuy(plan: PlanType) {
    if (plan === "free_trial") {
      await startFreeTrial();
      return;
    }
    await startStripeCheckout(plan);
  }

  return (
    <div className="flex flex-col min-h-screen bg-white selection:bg-accent/10">
      {/* Header */}
      <header className="absolute top-0 z-50 flex w-full pt-6">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 md:px-8 text-zinc-900 border-b border-zinc-100 pb-4">
          <div className="flex items-center gap-8">
            <Link className="inline-flex items-center justify-center font-serif text-2xl font-bold tracking-tight hover:text-accent transition-colors" href="/">
              LinkdApply
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" href="/#features">
                Features
              </Link>
              <Link className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" href="/#how-it-works">
                How it works
              </Link>
              <Link className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" href="/#faq">
                FAQ
              </Link>
              <Link className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" href="/pricing">
                Pricing
              </Link>
              <Link className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" href="/about">
                About
              </Link>
              <Link className="text-sm font-medium text-accent hover:text-accent/80 transition-colors" href="#download">
                Download
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <Link 
              className="hidden sm:inline-flex text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors" 
              href="/login"
            >
              Sign in
            </Link>
            <Link 
              className="purple-gradient-button inline-flex items-center justify-center rounded-full px-6 py-2.5 text-sm font-semibold text-white transition-all hover:scale-[1.02]" 
              href="/login"
            >
              Sign up
            </Link>
          </div>
        </div>
      </header>

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
          </div>

          <div className="mt-20 space-y-12 lg:space-y-0 lg:grid lg:grid-cols-4 lg:gap-x-4 items-stretch mb-24">
            {PLANS.map((plan) => (
              <PricingCard 
                key={plan.key}
                title={plan.title}
                price={plan.price}
                symbol="$"
                suffix={plan.suffix}
                description={plan.description}
                features={plan.features}
                loading={loading === plan.key}
                onBuy={() => handleBuy(plan.key as PlanType)}
                accent={plan.highlighted}
                badge={plan.badge}
              />
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-12 border-t border-zinc-100 bg-white">
        <div className="mx-auto max-w-7xl px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-8">
          <span className="font-serif text-2xl font-bold tracking-tight text-zinc-900">LinkdApply</span>
          <div className="flex gap-10 text-sm font-medium text-zinc-500">
            <Link href="/about" className="hover:text-zinc-900 transition-colors">About</Link>
            <Link href="/terms" className="hover:text-zinc-900 transition-colors">Terms</Link>
            <Link href="/privacy" className="hover:text-zinc-900 transition-colors">Privacy</Link>
            <Link href="/support" className="hover:text-zinc-900 transition-colors">Support</Link>
          </div>
          <p className="text-xs font-bold text-zinc-400 tracking-[0.2em] uppercase">© 2026 LinkdApply v1.1.0. All Rights Reserved.</p>
        </div>
      </footer>
    </div>
  );
}

function PricingCard({ title, price, symbol, suffix, description, features, loading, onBuy, accent, badge }: any) {
  return (
    <div className={`relative p-8 rounded-3xl transition-all flex flex-col ${
      accent 
      ? "bg-white border-2 border-accent shadow-2xl scale-105 z-10" 
      : "bg-zinc-50/50 border border-zinc-100 shadow-lg hover:bg-white hover:border-accent/20 hover:shadow-xl"
    }`}>
      {badge && (
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 px-4 py-1.5 bg-accent text-white text-[10px] font-bold uppercase tracking-widest rounded-full shadow-lg whitespace-nowrap">
          {badge}
        </div>
      )}
      <div className="flex-1">
        <h3 className="text-xl font-bold text-zinc-900">{title}</h3>
        <div className="mt-4 flex items-baseline gap-1">
          <span className="text-5xl font-extrabold tracking-tight text-zinc-900">{symbol}{price}</span>
          <span className="text-zinc-500 font-medium">/{suffix}</span>
        </div>
        <p className="mt-6 text-sm text-zinc-500 leading-relaxed min-h-[40px]">{description}</p>
        <ul className="mt-8 space-y-4">
          {features.map((f: string, i: number) => (
            <li key={i} className="flex items-start gap-3 text-sm text-zinc-600">
              <svg className="size-5 text-accent shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              <span>{f}</span>
            </li>
          ))}
        </ul>
      </div>
      <button
        onClick={onBuy}
        disabled={loading}
        className={`mt-10 w-full py-4 rounded-xl font-bold transition-all hover:scale-[1.02] disabled:opacity-50 ${
          accent 
          ? "purple-gradient-button text-white shadow-xl" 
          : "bg-white border border-zinc-200 text-zinc-900 shadow-sm hover:border-accent/20"
        }`}
      >
        {loading ? "Processing..." : title === "Free Trial" ? "Start Free Trial" : `Subscribe ${title}`}
      </button>
    </div>
  );
}
