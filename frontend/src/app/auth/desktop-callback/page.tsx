"use client";

import React, { Suspense, useEffect, useState } from "react";
import LandingBackground from "@/components/LandingBackground";

function DesktopCallbackContent() {
  const [deepLink, setDeepLink] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/auth/desktop/exchange", {
      method: "POST",
      credentials: "include",
    })
      .then(async (res) => {
        if (!res.ok) {
          throw new Error("Not signed in");
        }
        const data = (await res.json()) as { token?: string };
        if (!data.token) {
          throw new Error("Missing handoff token");
        }
        const link = `linkdapply://auth?token=${encodeURIComponent(data.token)}`;
        setDeepLink(link);
        window.location.href = link;
      })
      .catch(() => {
        setError(
          "Could not finish sign-in. Return to LinkdApply and try again."
        );
      });
  }, []);

  return (
    <div className="min-h-screen bg-white text-zinc-900 flex items-center justify-center p-6 overflow-hidden">
      <LandingBackground />
      <div className="relative z-10 max-w-md w-full text-center space-y-6">
          <h1 className="font-serif text-2xl font-semibold text-zinc-900">Sign-in complete</h1>
          {error ? (
            <p className="text-amber-800 text-sm bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">{error}</p>
          ) : (
            <>
              <p className="text-zinc-500 text-sm">
                Returning you to the LinkdApply desktop app…
              </p>
              <div className="size-6 mx-auto animate-spin rounded-full border-2 border-zinc-200 border-t-accent" />
              {deepLink ? (
                <p className="text-zinc-500 text-xs">
                  If the app did not open,{" "}
                  <a href={deepLink} className="text-accent hover:text-accent/80">
                    click here to open LinkdApply
                  </a>
                  .
                </p>
              ) : null}
            </>
          )}
        </div>
    </div>
  );
}

export default function DesktopCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-white flex items-center justify-center">
          <div className="size-6 animate-spin rounded-full border-2 border-zinc-200 border-t-accent" />
        </div>
      }
    >
      <DesktopCallbackContent />
    </Suspense>
  );
}
