/**
 * Windows installer is published via electron-builder to GitHub Releases.
 * Override with NEXT_PUBLIC_WINDOWS_INSTALLER_URL when hosting a mirror or staged rollout.
 */
export const WINDOWS_INSTALLER_URL =
  process.env.NEXT_PUBLIC_WINDOWS_INSTALLER_URL ??
  "https://github.com/yhimanshu22/Auto_job_applier_linkedIn/releases/latest/download/LinkdApply-Setup.exe";

export const RELEASES_PAGE_URL =
  process.env.NEXT_PUBLIC_RELEASES_PAGE_URL ??
  "https://github.com/yhimanshu22/Auto_job_applier_linkedIn/releases/latest";
