"use client";

import React, { Suspense } from "react";
import Link from "next/link";
import { getProviders, signIn, useSession } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";

import {
  desktopGoogleSignInUrl,
  shouldUseExternalDesktopAuth,
} from "@/lib/desktop-auth";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";
  const { status } = useSession();
  const [isLoading, setIsLoading] = React.useState(false);
  const [authError, setAuthError] = React.useState<string | null>(null);

  React.useEffect(() => {
    try {
      if (searchParams.get("desktop") === "1") {
        localStorage.setItem("linkdapply_desktop", "1");
      }
    } catch {
      /* blocked storage */
    }
  }, [searchParams]);

  React.useEffect(() => {
    if (status === "authenticated") {
      router.push(callbackUrl);
    }
  }, [status, router, callbackUrl]);

  React.useEffect(() => {
    getProviders().then((providers) => {
      if (!providers?.google) {
        setAuthError(
          "Google sign-in is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to frontend/.env.local, then restart the dev server."
        );
      }
    });
  }, []);

  const handleGoogleSignIn = () => {
    if (isLoading || authError) return;
    setIsLoading(true);

    if (shouldUseExternalDesktopAuth()) {
      // Tauri intercepts this navigation and opens the system browser for Google OAuth.
      window.location.href = desktopGoogleSignInUrl();
      return;
    }

    signIn("google", { callbackUrl });
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col selection:bg-accent/30">
      <div className="grow flex items-center justify-center p-6 bg-[radial-gradient(circle_at_top_right,rgba(124,58,237,0.1),transparent_50%)]">
        <div className="w-full max-w-md space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="text-center">
            <p className="font-serif text-3xl sm:text-4xl font-bold tracking-tight mb-4 bg-gradient-to-r from-indigo-300 via-blue-300 to-violet-300 bg-clip-text text-transparent">
              LinkdApply
            </p>
            <h1 className="font-serif text-3xl font-medium tracking-tight text-white">Welcome</h1>
            <p className="mt-2 text-zinc-500">The most powerful AI job application tool.</p>
            {shouldUseExternalDesktopAuth() ? (
              <p className="mt-3 text-xs text-zinc-500">
                Sign-in opens in your default browser, then returns to the desktop app.
              </p>
            ) : null}
          </div>

          <div className="glass-card rounded-3xl p-8 border border-zinc-800/50 shadow-2xl space-y-6">
            {authError ? (
              <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
                {authError}
              </p>
            ) : null}

            <div className="space-y-4">
              <button 
                onClick={handleGoogleSignIn}
                disabled={isLoading || Boolean(authError)}
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

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
          <div className="size-6 animate-spin rounded-full border-2 border-zinc-700 border-t-blue-500" />
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
