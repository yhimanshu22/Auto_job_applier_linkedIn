"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

import { apiFetch, isDesktopApp } from "@/lib/desktop-api";

/** Ask the backend to stop the job bot when leaving the dashboard. */
function requestStopJobBot(userId: string | null | undefined) {
  if (!userId) return;
  try {
    apiFetch("/api/bot/stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
      credentials: "include",
      keepalive: true,
    }).catch(() => {});
  } catch {
    /* page may already be tearing down */
  }
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const userId = session?.user?.email;

  useEffect(() => {
    if (status === "unauthenticated") {
      const callback = isDesktopApp()
        ? "/dashboard?desktop=1"
        : "/dashboard";
      router.replace(
        `/login?callbackUrl=${encodeURIComponent(callback)}${isDesktopApp() ? "&desktop=1" : ""}`
      );
    }
  }, [status, router]);

  // Stop the bot only when navigating away from the dashboard (not on tab hide /
  // alt-tab — pagehide was stopping a running bot in the desktop app).
  useEffect(() => {
    return () => {
      requestStopJobBot(userId);
    };
  }, [userId]);

  if (status !== "authenticated") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950">
        <div className="size-6 animate-spin rounded-full border-2 border-zinc-700 border-t-blue-500" />
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      <main className="flex-1 overflow-auto bg-zinc-50 dark:bg-zinc-950">
        {children}
      </main>
    </div>
  );
}
