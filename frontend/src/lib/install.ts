export type InstallOs = "windows" | "mac" | "linux";

export const REPO_OWNER = "yhimanshu22";
export const REPO_NAME = "Auto_job_applier_linkedIn";
export const GITHUB_RELEASES_URL = `https://github.com/${REPO_OWNER}/${REPO_NAME}/releases`;

export function getDesktopDownloadUrl(_os: InstallOs): string {
  return GITHUB_RELEASES_URL;
}

/** Build the desktop installer from source (until GitHub Releases are published). */
export function getInstallCommand(os: InstallOs): string {
  const repo = `https://github.com/${REPO_OWNER}/${REPO_NAME}.git`;
  const lines = [
    `git clone ${repo}`,
    "cd Auto_job_applier_linkedIn/desktop",
    "npm install",
    "npm run build:backend",
    "npm run build",
  ];
  if (os === "windows") {
    return lines.join("\r\n");
  }
  return lines.join("\n");
}

/** Client-only — call from useEffect, not during SSR or initial render. */
export function detectInstallOs(): InstallOs {
  if (typeof navigator === "undefined") return "windows";
  const ua = navigator.userAgent.toLowerCase();
  if (ua.includes("win")) return "windows";
  if (ua.includes("mac")) return "mac";
  return "linux";
}
