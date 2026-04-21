"use client";

import React from "react";
import Link from "next/link";
import { signIn } from "next-auth/react";
import TitleBar from "@/components/TitleBar";

export default function LoginPage() {
  const [electronAPI, setElectronAPI] = React.useState<any>(null);
  const [isLoading, setIsLoading] = React.useState(false);

  React.useEffect(() => {
    if (typeof window !== "undefined" && (window as any).electron) {
      console.log("[LoginPage] Electron API detected in window");
      setElectronAPI((window as any).electron);
    }
  }, []);

  const handleGoogleSignIn = () => {
    if (isLoading) return;
    setIsLoading(true);

    // Direct, real-time check of the window object
    const api = typeof window !== "undefined" ? (window as any).electron : null;
    
    if (api && typeof api.openExternal === "function") {
        console.log("[LoginPage] Triggering external browser auth via IPC...");
        // Use the deep link directly as callbackUrl
        const authUrl = `http://localhost:3000/api/auth/signin/google?callbackUrl=http://localhost:3000/auth-success`;
        try {
            api.openExternal(authUrl);
        } catch (err) {
            console.error("[LoginPage] IPC Call failed:", err);
            signIn("google", { callbackUrl: "/dashboard" });
            setIsLoading(false);
        }
    } else {
        console.log("[LoginPage] Electron API not found, using browser fallback...");
        signIn("google", { callbackUrl: "/dashboard" });
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col selection:bg-accent/30">
      <TitleBar />
      <div className="grow flex items-center justify-center p-6 bg-[radial-gradient(circle_at_top_right,rgba(124,58,237,0.1),transparent_50%)]">
        <div className="w-full max-w-md space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="text-center">
            <div className="inline-flex items-center justify-center size-16 rounded-2xl bg-accent/10 border border-accent/20 mb-6">
                <div className="size-8 rounded-lg bg-accent flex items-center justify-center text-white font-serif font-bold text-2xl shadow-xl shadow-accent/20">A</div>
            </div>
            <h1 className="font-serif text-4xl font-medium tracking-tight text-white">Welcome to LinkdApply</h1>
            <p className="mt-2 text-zinc-500">The most powerful AI job application tool.</p>
          </div>

          <div className="glass-card rounded-3xl p-8 border border-zinc-800/50 shadow-2xl space-y-6">
            <div className="space-y-4">
              <button 
                onClick={handleGoogleSignIn}
                disabled={isLoading}
                className={`w-full h-14 rounded-xl bg-white text-zinc-950 font-bold hover:bg-zinc-200 transition-all flex items-center justify-center gap-4 group shadow-xl ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="size-4 border-2 border-zinc-950/20 border-t-zinc-950 rounded-full animate-spin"></div>
                    <span>Connecting...</span>
                  </div>
                ) : (
                  <>
                    <svg className="size-6 group-hover:scale-110 transition-transform" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.14-4.53z"/>
                    </svg>
                    <span>Continue with Google</span>
                  </>
                )}
              </button>
            </div>

            <p className="text-center text-[10px] text-zinc-500 uppercase tracking-widest leading-relaxed">
                By continuing, you agree to our <br/>
                <Link href="/terms" className="text-zinc-400 hover:text-white transition-colors">Terms of Service</Link> and <Link href="/privacy" className="text-zinc-400 hover:text-white transition-colors">Privacy Policy</Link>
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}
