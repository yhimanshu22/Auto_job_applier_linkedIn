"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import TitleBar from "@/components/TitleBar";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Simulate login for now
    setTimeout(() => {
      setIsLoading(false);
      router.push("/dashboard");
    }, 1500);
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
            <h1 className="font-serif text-4xl font-medium tracking-tight text-white">Welcome Back</h1>
            <p className="mt-2 text-zinc-500">Sign in to manage your AI job applications.</p>
          </div>

          <div className="glass-card rounded-3xl p-8 border border-zinc-800/50 shadow-2xl space-y-6">
            <form onSubmit={handleLogin} className="space-y-5">
              <div className="space-y-2">
                <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest ml-1">Email Address</label>
                <input 
                  type="email" 
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all placeholder:text-zinc-700" 
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center px-1">
                    <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Password</label>
                    <button type="button" className="text-[10px] text-accent font-bold uppercase tracking-widest hover:text-white transition-colors">Forgot?</button>
                </div>
                <input 
                  type="password" 
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all placeholder:text-zinc-700" 
                />
              </div>

              <button 
                type="submit" 
                disabled={isLoading}
                className="w-full purple-gradient-button h-12 rounded-xl text-white font-bold shadow-2xl hover:scale-[1.01] transition-all flex items-center justify-center relative overflow-hidden"
              >
                {isLoading ? (
                  <div className="size-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  "Sign In"
                )}
              </button>
            </form>

            <div className="text-center pt-2">
                <p className="text-sm text-zinc-500">
                    Don't have an account?{" "}
                    <Link href="/signup" className="text-white hover:text-accent font-semibold transition-colors underline decoration-accent/30 underline-offset-4">
                        Create One
                    </Link>
                </p>
            </div>
          </div>

          <div className="flex items-center justify-center gap-6 text-[10px] text-zinc-600 font-bold uppercase tracking-[0.2em]">
              <Link href="/terms" className="hover:text-zinc-400">Terms</Link>
              <div className="size-1 rounded-full bg-zinc-800" />
              <Link href="/privacy" className="hover:text-zinc-400">Privacy</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
