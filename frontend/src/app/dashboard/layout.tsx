"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

import { apiFetch, isDesktopApp } from "@/lib/desktop-api";

/** Ask the backend to stop the job bot (tab close, navigate away, or layout unmount). */
function requestStopJobBot() {
  try {
    apiFetch("/api/bot/stop", {
      method: "POST",
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
  const { status } = useSession();
  const router = useRouter();

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

  useEffect(() => {
    const onPageHide = () => requestStopJobBot();
    window.addEventListener("pagehide", onPageHide);
    return () => {
      window.removeEventListener("pagehide", onPageHide);
      requestStopJobBot();
    };
  }, []);

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
