"use client";

import { SessionProvider } from "next-auth/react";
import { useEffect } from "react";

function useDevChunkReload() {
  useEffect(() => {
    if (process.env.NODE_ENV !== "development") return;

    const reloadOnChunkError = (message: string) => {
      if (message.includes("ChunkLoadError") || message.includes("Loading chunk")) {
        window.location.reload();
      }
    };

    const onError = (event: ErrorEvent) => reloadOnChunkError(event.message ?? "");
    const onRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      const message =
        typeof reason === "string"
          ? reason
          : reason instanceof Error
            ? reason.message
            : "";
      reloadOnChunkError(message);
    };

    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onRejection);
    return () => {
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onRejection);
    };
  }, []);
}

export default function AuthContext({ children }: { children: React.ReactNode }) {
  useDevChunkReload();

  return (
    <SessionProvider refetchOnWindowFocus={false} refetchInterval={0}>
      {children}
    </SessionProvider>
  );
}
