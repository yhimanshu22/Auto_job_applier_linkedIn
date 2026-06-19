"use client";

import { useEffect, useState } from "react";

export default function ProductHuntBanner() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if user dismissed it in this session
    const isDismissed = sessionStorage.getItem("ph_banner_dismissed");
    if (isDismissed) return;

    const urlParams = new URLSearchParams(window.location.search);
    const isPhReferral = 
      urlParams.get("utm_source") === "producthunt" || 
      urlParams.get("ref") === "producthunt" ||
      document.referrer.includes("producthunt.com");

    if (isPhReferral) {
      setIsVisible(true);
    }
  }, []);

  if (!isVisible) return null;

  return (
    <div className="w-full bg-gradient-to-r from-amber-500 via-orange-600 to-violet-700 text-white text-xs sm:text-sm font-medium py-2.5 px-4 sm:px-6 flex items-center justify-between gap-4 z-[60] relative shadow-md animate-in slide-in-from-top duration-300">
      <div className="flex-1 flex items-center justify-center gap-2 flex-wrap text-center">
        <span className="inline-flex items-center gap-1 bg-white/20 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider whitespace-nowrap">
          🐱 Product Hunt Exclusive
        </span>
        <span>
          Welcome PH community! Use code <strong className="font-bold underline decoration-white/50 bg-white/10 px-1.5 py-0.5 rounded">PH20</strong> for 20% off your first month of LinkdApply Pro.
        </span>
      </div>
      <button
        onClick={() => {
          setIsVisible(false);
          sessionStorage.setItem("ph_banner_dismissed", "true");
        }}
        className="text-white/80 hover:text-white transition-colors p-1 rounded-md hover:bg-white/10 shrink-0"
        aria-label="Dismiss banner"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
  );
}
