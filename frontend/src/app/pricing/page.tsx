"use client";

import React, { useState } from 'react';

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null);

  async function startCheckout(plan: "starter" | "pro" | "agency") {
    setLoading(plan);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/billing/create-checkout-session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          plan,
          user_id: "local-user",
          email: "user@example.com",
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed to start checkout");
      }

      window.location.href = data.url;
    } catch (error) {
      console.error(error);
      alert("Failed to initiate checkout. Is the backend running?");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="min-h-screen bg-white text-zinc-900 py-24 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[800px] hero-gradient opacity-10 pointer-events-none"></div>
      
      <div className="max-w-7xl mx-auto relative z-10">
        <div className="text-center space-y-4">
          <h2 className="text-sm font-bold text-accent tracking-[0.2em] uppercase">Pricing</h2>
          <p className="font-serif text-[40px] lg:text-[56px] leading-[1.1] font-medium tracking-tight text-zinc-900">
            Choose the right plan for your bot
          </p>
          <p className="max-w-2xl text-lg lg:text-xl text-zinc-500 mx-auto">
            Scale your LinkedIn automation safely and securely.
          </p>
        </div>

        <div className="mt-20 space-y-12 lg:space-y-0 lg:grid lg:grid-cols-3 lg:gap-x-8 items-center">
          {/* Starter Plan */}
          <div className="relative p-8 bg-zinc-50/50 border border-zinc-100 rounded-3xl shadow-lg flex flex-col hover:bg-white hover:border-accent/20 transition-all hover:shadow-xl">
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-zinc-900">Starter</h3>
              <p className="mt-4 flex items-baseline text-zinc-900">
                <span className="text-5xl font-extrabold tracking-tight">$19</span>
                <span className="ml-1 text-xl font-medium text-zinc-500">/mo</span>
              </p>
              <p className="mt-6 text-zinc-500">For individuals getting started with automation.</p>
              <ul role="list" className="mt-8 space-y-6">
                <li className="flex items-center text-zinc-600"><span className="text-accent mr-3 font-bold text-lg">✓</span>1 LinkedIn account</li>
                <li className="flex items-center text-zinc-600"><span className="text-accent mr-3 font-bold text-lg">✓</span>1 Active Bot</li>
                <li className="flex items-center text-zinc-600"><span className="text-accent mr-3 font-bold text-lg">✓</span>100 applications / month</li>
              </ul>
            </div>
            <button
              onClick={() => startCheckout("starter")}
              disabled={loading === "starter"}
              className="mt-8 block w-full py-4 px-6 border border-zinc-200 rounded-xl text-center font-semibold text-zinc-900 bg-white hover:bg-zinc-50 transition-all disabled:opacity-50 shadow-sm"
            >
              {loading === "starter" ? "Loading..." : "Get Started"}
            </button>
          </div>

          {/* Pro Plan */}
          <div className="relative p-8 bg-white border-2 border-accent/30 rounded-3xl shadow-2xl flex flex-col transform lg:-translate-y-4">
            <div className="absolute top-0 py-1.5 px-4 bg-accent rounded-full text-xs font-bold uppercase tracking-widest text-white transform -translate-y-1/2 left-1/2 -translate-x-1/2 shadow-lg">
              Most Popular
            </div>
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-zinc-900">Pro</h3>
              <p className="mt-4 flex items-baseline text-zinc-900">
                <span className="text-6xl font-extrabold tracking-tight">$49</span>
                <span className="ml-1 text-xl font-medium text-zinc-500">/mo</span>
              </p>
              <p className="mt-6 text-zinc-500">For power users and small teams.</p>
              <ul role="list" className="mt-8 space-y-6">
                <li className="flex items-center text-zinc-600"><span className="text-accent mr-3 font-bold text-lg">✓</span>3 LinkedIn accounts</li>
                <li className="flex items-center text-zinc-600"><span className="text-accent mr-3 font-bold text-lg">✓</span>2 Active Bots</li>
                <li className="flex items-center text-zinc-600"><span className="text-accent mr-3 font-bold text-lg">✓</span>500 applications / month</li>
                <li className="flex items-center text-zinc-600"><span className="text-accent mr-3 font-bold text-lg">✓</span>AI dynamic answers</li>
              </ul>
            </div>
            <button
              onClick={() => startCheckout("pro")}
              disabled={loading === "pro"}
              className="mt-8 block w-full py-4 px-6 rounded-xl text-center font-semibold text-white purple-gradient-button hover:scale-[1.02] transition-all disabled:opacity-50 shadow-xl"
            >
              {loading === "pro" ? "Loading..." : "Upgrade to Pro"}
            </button>
          </div>

          {/* Agency Plan */}
          <div className="relative p-8 bg-zinc-50/50 border border-zinc-100 rounded-3xl shadow-lg flex flex-col hover:bg-white hover:border-accent/20 transition-all hover:shadow-xl">
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-zinc-900">Agency</h3>
              <p className="mt-4 flex items-baseline text-zinc-900">
                <span className="text-5xl font-extrabold tracking-tight">$149</span>
                <span className="ml-1 text-xl font-medium text-zinc-500">/mo</span>
              </p>
              <p className="mt-6 text-zinc-500">For scaling recruitment teams and agencies.</p>
              <ul role="list" className="mt-8 space-y-6">
                <li className="flex items-center text-zinc-600"><span className="text-accent mr-3 font-bold text-lg">✓</span>10+ LinkedIn accounts</li>
                <li className="flex items-center text-zinc-600"><span className="text-accent mr-3 font-bold text-lg">✓</span>5 Active Bots</li>
                <li className="flex items-center text-zinc-600"><span className="text-accent mr-3 font-bold text-lg">✓</span>3000 applications / month</li>
                <li className="flex items-center text-zinc-600"><span className="text-accent mr-3 font-bold text-lg">✓</span>Priority support</li>
              </ul>
            </div>
            <button
              onClick={() => startCheckout("agency")}
              disabled={loading === "agency"}
              className="mt-8 block w-full py-4 px-6 border border-zinc-200 rounded-xl text-center font-semibold text-zinc-900 bg-white hover:bg-zinc-50 transition-all disabled:opacity-50 shadow-sm"
            >
              {loading === "agency" ? "Loading..." : "Go Agency"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
