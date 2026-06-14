import { isDesktopApp } from "@/lib/desktop-api";

/** Build the Google sign-in URL used by the desktop app (opened in system browser). */
export function desktopGoogleSignInUrl(): string {
  const origin = window.location.origin;
  const callback = `${origin}/auth/desktop-callback?desktop=1`;
  return `${origin}/api/auth/signin/google?callbackUrl=${encodeURIComponent(callback)}`;
}

export function shouldUseExternalDesktopAuth(): boolean {
  return isDesktopApp();
}
