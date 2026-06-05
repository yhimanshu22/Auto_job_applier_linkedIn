export type InstallOs = "windows" | "mac" | "linux";

export const REPO_OWNER = "yhimanshu22";
export const REPO_NAME = "Auto_job_applier_linkedIn";
export const INSTALL_BRANCH = "main";

export function rawInstallScriptUrl(path: "install.sh" | "install.ps1") {
  return `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${INSTALL_BRANCH}/${path}`;
}

export function getInstallCommand(os: InstallOs): string {
  const sh = `curl -fsSL "${rawInstallScriptUrl("install.sh")}" | bash`;
  const ps = `powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr -useb '${rawInstallScriptUrl("install.ps1")}' | iex"`;
  return os === "windows" ? ps : sh;
}

/** Client-only — call from useEffect, not during SSR or initial render. */
export function detectInstallOs(): InstallOs {
  if (typeof navigator === "undefined") return "windows";
  const ua = navigator.userAgent.toLowerCase();
  if (ua.includes("win")) return "windows";
  if (ua.includes("mac")) return "mac";
  return "linux";
}
