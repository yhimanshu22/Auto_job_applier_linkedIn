/** Server-only release host config (never import from client components). */
export function getReleaseRepo(): { owner: string; name: string } | null {
  const owner =
    process.env.GITHUB_RELEASE_OWNER?.trim() || "yhimanshu22";
  const name =
    process.env.GITHUB_RELEASE_REPO?.trim() || "Auto_job_applier_linkedIn";
  if (!owner || !name) return null;
  return { owner, name };
}
