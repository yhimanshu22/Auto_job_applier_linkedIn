/** Shared NEXTAUTH_SECRET resolution for API routes. */
export function resolveAuthSecret(): string | undefined {
  const env = process.env.NEXTAUTH_SECRET?.trim();
  if (env) return env;
  if (process.env.NODE_ENV !== "production") {
    return "local-dev-only-nextauth-secret-not-for-production";
  }
  return undefined;
}
