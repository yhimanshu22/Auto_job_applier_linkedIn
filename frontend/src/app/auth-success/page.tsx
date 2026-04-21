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
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center text-white">
      <div className="space-y-4 text-center">
        <div className="size-12 border-4 border-accent/30 border-t-accent rounded-full animate-spin mx-auto"></div>
        <h1 className="text-2xl font-serif">Authentication Successful</h1>
        <p className="text-zinc-500">Returning you to the LinkdApply app...</p>
        <p className="text-[10px] text-zinc-700 uppercase tracking-widest mt-8">You can close this tab now</p>
      </div>
    </div>
  );
}
