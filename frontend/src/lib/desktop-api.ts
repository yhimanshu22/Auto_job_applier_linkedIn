/**
 * Desktop (Tauri) thin launcher:
 * - Local sidecar: configs, secrets, bot, automation, applications, uploads
 * - Hosted cloud API: billing, auth (NextAuth), subscription checkout only
 */

const LOCAL_API_PREFIXES = [
  "/api/bot",
  "/api/config",
  "/api/linkedin-automation",
  "/api/applications",
  "/api/upload",
  "/api/health",
];

const CLOUD_API_PREFIXES = ["/api/billing"];

const LOCAL_API_DEFAULT = "http://127.0.0.1:8000";

declare global {
  interface Window {
    __LINKDAPPLY_DESKTOP__?: { localApi?: string };
  }
}

/** True when opened from the Tauri app (?desktop=1 or injected flag). */
export function isDesktopApp(): boolean {
  if (typeof window === "undefined") return false;
  if (window.__LINKDAPPLY_DESKTOP__) return true;
  try {
    if (localStorage.getItem("linkdapply_desktop") === "1") return true;
    const params = new URLSearchParams(window.location.search);
    if (params.get("desktop") === "1") {
      localStorage.setItem("linkdapply_desktop", "1");
      return true;
    }
  } catch {
    /* private mode / blocked storage */
  }
  return false;
}

export function localApiBase(): string {
  const injected = window.__LINKDAPPLY_DESKTOP__?.localApi?.trim();
  if (injected) return injected.replace(/\/$/, "");
  const env = process.env.NEXT_PUBLIC_LOCAL_BOT_API?.trim();
  if (env) return env.replace(/\/$/, "");
  return LOCAL_API_DEFAULT;
}

/** Session email for API query params (undefined while NextAuth is loading). */
export function encodeUserId(userId: string | null | undefined): string {
  return encodeURIComponent(userId ?? "");
}

function usesLocalSidecar(path: string): boolean {
  if (!isDesktopApp()) return false;
  if (CLOUD_API_PREFIXES.some((prefix) => path.startsWith(prefix))) {
    return false;
  }
  return LOCAL_API_PREFIXES.some((prefix) => path.startsWith(prefix));
}

/** Resolve /api/... to the local sidecar when running inside the desktop app. */
export function apiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (usesLocalSidecar(normalized)) {
    return `${localApiBase()}${normalized}`;
  }
  return normalized;
}

/** Drop-in fetch wrapper for dashboard API calls. */
export async function apiFetch(
  path: string,
  init?: RequestInit
): Promise<Response> {
  return fetch(apiUrl(path), {
    credentials: "include",
    ...init,
  });
}
