"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

type PlanType = "starter" | "pro" | "agency";

const PRICING = {
  USD: {
    symbol: "$",
    starter: 15,
    pro: 30,
    agency: 60,
  },
  INR: {
    symbol: "₹",
    starter: 1000,
    pro: 2000,
    agency: 4000,
  }
};

const RAZORPAY_KEY_ID = "rzp_test_Sk0DHEFDwbgFb2";

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null);
  const [region, setRegion] = useState<"USD" | "INR">("INR");
  const [sdkReady, setSdkReady] = useState(false);

  // Resilient script loading
  useEffect(() => {
    const checkSdk = () => {
      if ((window as any).Razorpay) {
        console.log("Razorpay SDK detected");
        setSdkReady(true);
        return true;
      }
      return false;
    };

    if (checkSdk()) return;

    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => {
      console.log("Razorpay SDK Loaded via useEffect");
      setSdkReady(true);
    };
    script.onerror = () => {
      console.error("Failed to load Razorpay SDK");
    };
    document.body.appendChild(script);

    // Periodic check as fallback
    const interval = setInterval(() => {
      if (checkSdk()) clearInterval(interval);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

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

  async function startRazorpayCheckout(plan: PlanType) {
    setLoading(plan);
    console.log(`Starting Razorpay checkout for ${plan}...`);
    try {
      const amount = PRICING.INR[plan];
      
      const res = await fetch("http://localhost:8000/api/razorpay/create-order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan, amount }),
      });
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Backend Error: ${res.status} - ${errorText}`);
      }

      const order = await res.json();
      console.log("Order created successfully:", order);

      const options = {
        key: RAZORPAY_KEY_ID,
        amount: order.amount,
        currency: order.currency,
        name: "LinkdApply",
        description: `Subscription for ${plan} plan`,
        order_id: order.id,
        handler: async function (response: any) {
          console.log("Payment Success Callback Received:", response);
          
          const verifyRes = await fetch("http://localhost:8000/api/razorpay/verify-payment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(response),
          });
          
          if (verifyRes.ok) {
            alert("Payment Verified! Your subscription is active.");
            window.location.href = "/billing/success";
          } else {
            alert("Payment received but verification failed. Please contact support.");
          }
        },
        modal: {
          ondismiss: function() {
            setLoading(null);
          }
        },
        prefill: {
          name: "User",
          email: "user@example.com",
        },
        theme: {
          color: "#6d28d9",
        },
      };

      const rzp = new (window as any).Razorpay(options);
      rzp.open();
      
    } catch (error: any) {
      console.error("Razorpay Integration Error:", error);
      alert(`Razorpay Error: ${error.message || "Failed to initialize checkout"}`);
    } finally {
      setLoading(null);
    }
  }

  function handleBuy(plan: PlanType) {
    if (region === "USD") {
      startStripeCheckout(plan);
    } else {
      if (!sdkReady) {
        alert("Payment system is still loading. Please wait a second or check your internet connection.");
        return;
      }
      startRazorpayCheckout(plan);
    }
  }

  return (
    <div className="min-h-screen bg-white text-zinc-900 py-24 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[800px] hero-gradient opacity-10 pointer-events-none"></div>
      
      <div className="max-w-7xl mx-auto relative z-10">
        <div className="text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-[10px] font-bold uppercase tracking-widest text-accent">
            Secure Payments via Stripe & Razorpay
          </div>
          <p className="font-serif text-[40px] lg:text-[64px] leading-[1.1] font-medium tracking-tight text-zinc-900">
            Choose your plan
          </p>
          
          <div className="flex items-center justify-center pt-4">
            <div className="bg-zinc-100 p-1 rounded-xl flex gap-1 border border-zinc-200">
              <button 
                onClick={() => setRegion("USD")}
                className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${region === "USD" ? "bg-white text-zinc-900 shadow-sm" : "text-zinc-500 hover:text-zinc-700"}`}
              >
                Global (USD)
              </button>
              <button 
                onClick={() => setRegion("INR")}
                className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${region === "INR" ? "bg-white text-zinc-900 shadow-sm" : "text-zinc-500 hover:text-zinc-700"}`}
              >
                India (INR)
              </button>
            </div>
          </div>
        </div>

        <div className="mt-20 space-y-12 lg:space-y-0 lg:grid lg:grid-cols-3 lg:gap-x-8 items-stretch">
          <PricingCard 
            title="Starter"
            price={PRICING[region].starter}
            symbol={PRICING[region].symbol}
            description="Perfect for individuals starting their job search."
            features={["1 LinkedIn account", "1 Active Bot", "100 applications / mo"]}
            loading={loading === "starter"}
            onBuy={() => handleBuy("starter")}
            accent={false}
          />

          <PricingCard 
            title="Pro"
            price={PRICING[region].pro}
            symbol={PRICING[region].symbol}
            description="Most popular for serious job seekers."
            features={["3 LinkedIn accounts", "2 Active Bots", "500 applications / mo", "AI dynamic answers"]}
            loading={loading === "pro"}
            onBuy={() => handleBuy("pro")}
            accent={true}
            badge="Most Popular"
          />

          <PricingCard 
            title="Agency"
            price={PRICING[region].agency}
            symbol={PRICING[region].symbol}
            description="For teams and heavy recruitment needs."
            features={["10+ LinkedIn accounts", "5 Active Bots", "3000 applications / mo", "Priority support"]}
            loading={loading === "agency"}
            onBuy={() => handleBuy("agency")}
            accent={false}
          />
        </div>
      </div>
    </div>
  );
}

function PricingCard({ title, price, symbol, description, features, loading, onBuy, accent, badge }: any) {
  return (
    <div className={`relative p-8 rounded-3xl transition-all flex flex-col ${
      accent 
      ? "bg-white border-2 border-accent shadow-2xl scale-105 z-10" 
      : "bg-zinc-50/50 border border-zinc-100 shadow-lg hover:bg-white hover:border-accent/20 hover:shadow-xl"
    }`}>
      {badge && (
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 px-4 py-1.5 bg-accent text-white text-[10px] font-bold uppercase tracking-widest rounded-full shadow-lg">
          {badge}
        </div>
      )}
      <div className="flex-1">
        <h3 className="text-xl font-bold text-zinc-900">{title}</h3>
        <div className="mt-4 flex items-baseline gap-1">
          <span className="text-5xl font-extrabold tracking-tight text-zinc-900">{symbol}{price}</span>
          <span className="text-zinc-500 font-medium">/mo</span>
        </div>
        <p className="mt-6 text-sm text-zinc-500 leading-relaxed">{description}</p>
        <ul className="mt-8 space-y-4">
          {features.map((f: string, i: number) => (
            <li key={i} className="flex items-center gap-3 text-sm text-zinc-600">
              <svg className="size-5 text-accent shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              {f}
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
        {loading ? "Processing..." : accent ? `Subscribe ${title}` : "Get Started"}
      </button>
    </div>
  );
}
