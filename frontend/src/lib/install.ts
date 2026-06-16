export type InstallOs = "windows" | "mac" | "linux";

/** From repo VERSION via next.config.ts (NEXT_PUBLIC_DESKTOP_VERSION). */
export const DESKTOP_VERSION =
  process.env.NEXT_PUBLIC_DESKTOP_VERSION?.trim() || "0.0.0";

const GITHUB_RELEASE_BASE = `https://github.com/yhimanshu22/Auto_job_applier_linkedIn/releases/download/v${DESKTOP_VERSION}`;

export const WINDOWS_INSTALLER_FILENAME = `LinkdApply_${DESKTOP_VERSION}_x64_en-US.msi`;
export const MAC_ARM_INSTALLER_FILENAME = `LinkdApply_${DESKTOP_VERSION}_aarch64.dmg`;
export const MAC_INTEL_INSTALLER_FILENAME = `LinkdApply_${DESKTOP_VERSION}_x64.dmg`;
export const LINUX_INSTALLER_FILENAME = `LinkdApply_${DESKTOP_VERSION}_amd64.AppImage`;

const ASSET_PATTERNS: Record<InstallOs, RegExp> = {
  windows: /\.msi$/i,
  mac: /\.dmg$/i,
  linux: /\.AppImage$/i,
};

/** macOS build is Apple Silicon (aarch64) for now. */
export function getMacInstallerFilename(): string {
  return MAC_ARM_INSTALLER_FILENAME;
}

export function getInstallerFilename(os: InstallOs): string {
  if (os === "windows") return WINDOWS_INSTALLER_FILENAME;
  if (os === "mac") return getMacInstallerFilename();
  return LINUX_INSTALLER_FILENAME;
}

export function getDesktopDownloadUrl(os: InstallOs): string {
  const overrides: Record<InstallOs, string | undefined> = {
    windows: process.env.NEXT_PUBLIC_WINDOWS_INSTALLER_URL,
    mac: process.env.NEXT_PUBLIC_MAC_INSTALLER_URL,
    linux: process.env.NEXT_PUBLIC_LINUX_INSTALLER_URL,
  };
  const override = overrides[os]?.trim();
  if (override) return override;

  return `${GITHUB_RELEASE_BASE}/${getInstallerFilename(os)}`;
}

/** @deprecated Use getDesktopDownloadUrl("windows") */
export const DEFAULT_WINDOWS_INSTALLER_URL = getDesktopDownloadUrl("windows");

export function isDownloadAvailable(_os: InstallOs): boolean {
  return true;
}

export function getAssetPattern(os: InstallOs): RegExp {
  return ASSET_PATTERNS[os];
}

export function getInstallerLabel(os: InstallOs): string {
  if (os === "windows") return "Windows .msi";
  if (os === "mac") return "macOS .dmg (Apple Silicon)";
  return "Linux .AppImage";
}

/** Client-only — call from useEffect, not during SSR or initial render. */
export function detectInstallOs(): InstallOs {
  if (typeof navigator === "undefined") return "windows";
  const ua = navigator.userAgent.toLowerCase();
  if (ua.includes("win")) return "windows";
  if (ua.includes("mac")) return "mac";
  return "linux";
}

export function getOsLabel(os: InstallOs): string {
  if (os === "windows") return "Windows";
  if (os === "mac") return "macOS";
  return "Linux";
}
