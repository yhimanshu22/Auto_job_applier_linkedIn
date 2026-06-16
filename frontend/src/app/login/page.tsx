"use client";

import React, { Suspense } from "react";
import Link from "next/link";
import { getProviders, signIn, useSession } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";

import LandingBackground from "@/components/LandingBackground";
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
  const [agreedToTerms, setAgreedToTerms] = React.useState(false);

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
    if (isLoading || authError || !agreedToTerms) return;
    setIsLoading(true);

    if (shouldUseExternalDesktopAuth()) {
      window.location.href = desktopGoogleSignInUrl();
      return;
    }

    signIn("google", { callbackUrl });
  };

  return (
    <div className="min-h-screen bg-white text-zinc-900 selection:bg-accent/10 flex flex-col">
      <div className="relative flex-1 flex items-center justify-center p-6 overflow-hidden">
        <LandingBackground />

        <div className="relative z-10 w-full max-w-md space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="text-center">
            <Link
              href="/"
              className="inline-block font-serif text-3xl sm:text-4xl font-bold tracking-tight mb-4 bg-gradient-to-r from-indigo-700 via-blue-700 to-violet-600 bg-clip-text text-transparent hover:opacity-90 transition-opacity"
            >
              LinkdApply
            </Link>
            <h1 className="font-serif text-3xl font-medium tracking-tight text-zinc-900">
              Welcome
            </h1>
            <p className="mt-2 text-zinc-500">
              Sign in or create your account to start automating applications.
            </p>
            {shouldUseExternalDesktopAuth() ? (
              <p className="mt-3 text-xs text-zinc-500">
                Sign-in opens in your default browser, then returns to the desktop app.
              </p>
            ) : null}
          </div>

          <div className="rounded-3xl border border-zinc-200 bg-white/90 backdrop-blur-sm p-8 shadow-xl shadow-zinc-200/50 space-y-6">
            {authError ? (
              <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                {authError}
              </p>
            ) : null}

            <div className="space-y-4">
              <label className="flex items-start gap-3 cursor-pointer text-left">
                <input
                  type="checkbox"
                  checked={agreedToTerms}
                  onChange={(e) => setAgreedToTerms(e.target.checked)}
                  className="mt-0.5 size-4 shrink-0 rounded border-zinc-300 text-accent focus:ring-accent/30"
                />
                <span className="text-sm text-zinc-600 leading-relaxed">
                  By continuing, you agree to our{" "}
                  <Link
                    href="/terms"
                    className="text-zinc-900 underline underline-offset-2 hover:text-accent"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Terms of Service
                  </Link>{" "}
                  and{" "}
                  <Link
                    href="/privacy"
                    className="text-zinc-900 underline underline-offset-2 hover:text-accent"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Privacy Policy
                  </Link>
                  .
                </span>
              </label>

              <button
                onClick={handleGoogleSignIn}
                disabled={isLoading || Boolean(authError) || !agreedToTerms}
                className={`btn-on-light w-full inline-flex items-center justify-center gap-4 px-10 py-4 font-bold shadow-xl transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed ${isLoading ? "opacity-70 cursor-not-allowed" : ""}`}
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="size-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    <span>Connecting...</span>
                  </div>
                ) : (
                  <>
                    <svg className="size-6 group-hover:scale-110 transition-transform" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.14-4.53z" />
                    </svg>
                    <span>Continue with Google</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AuthPageFallback() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center overflow-hidden">
      <LandingBackground />
      <div className="relative z-10 size-6 animate-spin rounded-full border-2 border-zinc-200 border-t-accent" />
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<AuthPageFallback />}>
      <LoginContent />
    </Suspense>
  );
}
