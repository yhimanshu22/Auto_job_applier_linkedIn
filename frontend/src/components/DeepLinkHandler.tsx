"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DeepLinkHandler() {
  const router = useRouter();

  useEffect(() => {
    // Check if we are running in Electron
    if (typeof window !== "undefined" && (window as any).electron?.onAuthSuccess) {
      console.log("[DeepLinkHandler] Listening for auth-success from Electron...");
      
      (window as any).electron.onAuthSuccess((token: string) => {
        console.log("[DeepLinkHandler] Received auth token from deep link:", token);
        
        // For now, we store the token in localStorage and redirect to dashboard
        // In a real app, you might want to sync this with your auth provider
        localStorage.setItem("auth_token", token);
        
        // Redirect to dashboard
        router.push("/dashboard");
      });
    }
  }, [router]);

  return null; // This component doesn't render anything
}
