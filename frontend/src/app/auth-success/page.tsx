"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AuthSuccessPage() {
  const router = useRouter();

  useEffect(() => {
    // This page is opened in the system browser after Google login
    // We want to trigger the deep link to return to Electron
    window.location.assign("linkdapply://auth-success");
    
    // Fallback for UI
    setTimeout(() => {
      router.push("/dashboard");
    }, 2000);
  }, [router]);

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center text-white p-6">
      <div className="max-w-sm w-full glass-card rounded-3xl p-8 border border-zinc-800/50 shadow-2xl space-y-6 text-center">
        <div className="size-16 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto mb-2 text-accent">
          <svg className="size-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        
        <h1 className="text-2xl font-serif font-bold">Authenticated!</h1>
        <p className="text-zinc-500 text-sm">We're opening the desktop app for you.</p>

        <div className="py-4">
          <button 
            onClick={() => window.location.assign("linkdapply://auth-success")}
            className="w-full h-12 rounded-xl purple-gradient-button text-white font-bold shadow-lg hover:scale-[1.02] transition-all"
          >
            Launch LinkdApply
          </button>
        </div>

        <p className="text-[10px] text-zinc-600 uppercase tracking-widest">
          You can safely close this window now
        </p>
      </div>
    </div>
  );
}
