"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import TitleBar from "@/components/TitleBar";

export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Simulate signup for now
    setTimeout(() => {
      setIsLoading(false);
      router.push("/dashboard");
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col selection:bg-accent/30">
      <TitleBar />
      <div className="grow flex items-center justify-center p-6 bg-[radial-gradient(circle_at_bottom_left,rgba(124,58,237,0.1),transparent_50%)]">
        <div className="w-full max-w-md space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="text-center">
            <div className="inline-flex items-center justify-center size-16 rounded-2xl bg-accent/10 border border-accent/20 mb-6">
                <div className="size-8 rounded-lg bg-accent flex items-center justify-center text-white font-serif font-bold text-2xl shadow-xl shadow-accent/20">A</div>
            </div>
            <h1 className="font-serif text-4xl font-medium tracking-tight text-white">Join LinkdApply</h1>
            <p className="mt-2 text-zinc-500">The first step to a smarter job search.</p>
          </div>

          <div className="glass-card rounded-3xl p-8 border border-zinc-800/50 shadow-2xl space-y-6">
            <form onSubmit={handleSignup} className="space-y-5">
              <div className="space-y-2">
                <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest ml-1">Full Name</label>
                <input 
                  type="text" 
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all placeholder:text-zinc-700" 
                />
              </div>

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
                <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest ml-1">Password</label>
                <input 
                  type="password" 
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a strong password"
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
                  "Create Account"
                )}
              </button>
            </form>

            <div className="text-center pt-2">
                <p className="text-sm text-zinc-500">
                    Already using LinkdApply?{" "}
                    <Link href="/login" className="text-white hover:text-accent font-semibold transition-colors underline decoration-accent/30 underline-offset-4">
                        Sign In
                    </Link>
                </p>
            </div>
          </div>

          <div className="text-center">
              <p className="text-[10px] text-zinc-600 leading-relaxed max-w-xs mx-auto">
                By signing up, you agree to our <Link href="/terms" className="underline decoration-zinc-800">Terms of Service</Link> and <Link href="/privacy" className="underline decoration-zinc-800">Privacy Policy</Link>.
              </p>
          </div>
        </div>
      </div>
    </div>
  );
}
