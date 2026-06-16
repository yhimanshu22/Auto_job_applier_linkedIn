import React from 'react';

function formatINR(amount: number) {
  return amount.toLocaleString('en-IN');
}

export default function PricingCard({ plan, billingCycle, currency = "usd", loading, onBuy }: any) {
  const isFreeTrial = plan.key === "free_trial";
  const isINR = currency === "inr";

  const price = isINR
    ? (billingCycle === "yearly" ? plan.inrYearlyMonthlyPrice : plan.inrMonthlyPrice)
    : (billingCycle === "yearly" ? plan.yearlyMonthlyPrice : plan.monthlyPrice);

  const symbol = isINR ? "₹" : "$";
  const displayPrice = isINR ? formatINR(price) : price;
  const accent = plan.highlighted;

  const yearlyTotalText = isINR
    ? `₹${formatINR(plan.inrYearlyTotal)}`
    : `$${plan.yearlyTotal}`;

  const billingText = isFreeTrial
    ? "Limited 24-hour access"
    : billingCycle === "yearly"
      ? `Billed yearly at ${yearlyTotalText}`
      : "Billed monthly";

  return (
    <div className={`relative p-8 rounded-3xl transition-all flex flex-col ${
      accent 
      ? "bg-white border-2 border-accent shadow-2xl scale-105 z-10" 
      : "bg-zinc-50/50 border border-zinc-100 shadow-lg hover:bg-white hover:border-accent/20 hover:shadow-xl"
    }`}>
      {plan.badge && (
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 px-4 py-1.5 bg-accent text-white text-[10px] font-bold uppercase tracking-widest rounded-full shadow-lg whitespace-nowrap">
          {plan.badge}
        </div>
      )}
      <div className="flex-1">
        <h3 className="text-xl font-bold text-zinc-900">{plan.title}</h3>
        <div className="mt-4 flex items-baseline gap-1">
          <span className="text-5xl font-extrabold tracking-tight text-zinc-900">{symbol}{displayPrice}</span>
          <span className="text-zinc-500 font-medium">
            {isFreeTrial ? "/trial" : "/mo"}
          </span>
        </div>
        <p className="mt-2 text-xs font-medium text-zinc-400">
          {billingText}
        </p>
        <p className="mt-6 text-sm text-zinc-500 leading-relaxed min-h-[40px]">{plan.description}</p>
        <ul className="mt-8 space-y-4">
          {plan.features.map((f: string, i: number) => (
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
        className={`mt-10 w-full inline-flex items-center justify-center gap-2 px-10 py-4 text-sm font-bold transition-all hover:scale-[1.02] disabled:opacity-50 ${
          accent
            ? "btn-on-light shadow-xl"
            : "btn-secondary-light"
        }`}
      >
        {loading ? "Processing..." : isFreeTrial ? "Start Free Trial" : `Subscribe ${plan.title}`}
      </button>
    </div>
  );
}
