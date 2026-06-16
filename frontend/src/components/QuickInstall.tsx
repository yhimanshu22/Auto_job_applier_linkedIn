"use client";

import { useEffect, useMemo, useState } from "react";
import DownloadLink, { DownloadIcon } from "@/components/DownloadLink";
import {
  DESKTOP_VERSION,
  LINUX_INSTALLER_FILENAME,
  MAC_ARM_INSTALLER_FILENAME,
  WINDOWS_INSTALLER_FILENAME,
  detectInstallOs,
  getInstallerFilename,
  getInstallerLabel,
  getOsLabel,
  type InstallOs,
} from "@/lib/install";

type QuickInstallProps = {
  id?: string;
  variant?: "section" | "compact";
};

const OS_TABS = [
  { id: "windows", label: "Windows" },
  { id: "mac", label: "macOS" },
  { id: "linux", label: "Linux" },
] as const;

const SSR_DEFAULT_OS: InstallOs = "windows";

export default function QuickInstall({ id, variant = "section" }: QuickInstallProps) {
  const [active, setActive] = useState<InstallOs>(SSR_DEFAULT_OS);

  useEffect(() => {
    setActive(detectInstallOs());
  }, []);

  const osLabel = getOsLabel(active);
  const installerLabel = useMemo(() => getInstallerLabel(active), [active]);
  const installerFilename = useMemo(() => getInstallerFilename(active), [active]);

  const downloadCta = (
    <DownloadLink
      os={active}
      className="inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-white purple-gradient-button shadow-md hover:scale-[1.02] transition-all"
    >
      <DownloadIcon />
      Download for {osLabel}
    </DownloadLink>
  );

  if (variant === "compact") {
    return (
      <div className="w-full max-w-2xl mx-auto space-y-3 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-500">
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          {downloadCta}
        </div>
        <p className="text-xs text-zinc-500 text-center">
          v{DESKTOP_VERSION} · {installerLabel}
        </p>
      </div>
    );
  }

  return (
    <section id={id} className="py-24 bg-white border-y border-zinc-100 scroll-mt-28">
      <div className="mx-auto max-w-4xl px-6 lg:px-8">
        <div className="text-center space-y-4 mb-10">
          <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900 leading-tight">
            Install the <span className="text-accent italic">desktop app</span>
          </h2>
          <p className="text-zinc-500">
            Download for Windows, macOS, or Linux. Run the installer, then sign in to start applying.
          </p>
        </div>

        <div className="rounded-3xl border border-zinc-200 bg-zinc-50 p-6 lg:p-8 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="inline-flex rounded-full border border-zinc-200 bg-white p-1">
              {OS_TABS.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setActive(t.id)}
                  className={[
                    "px-4 py-2 text-xs font-bold uppercase tracking-widest rounded-full transition-colors",
                    active === t.id
                      ? "bg-zinc-900 text-white"
                      : "text-zinc-600 hover:text-zinc-900",
                  ].join(" ")}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <DownloadLink
              os={active}
              className="inline-flex items-center justify-center gap-2 rounded-full px-6 py-2.5 text-sm font-semibold text-white purple-gradient-button shadow-md hover:scale-[1.02] transition-all"
            >
              <DownloadIcon />
              Download v{DESKTOP_VERSION}
            </DownloadLink>
          </div>

          <div className="rounded-2xl border border-zinc-200 bg-white p-5 text-sm text-zinc-600 space-y-2">
            <p>
              <span className="font-semibold text-zinc-900">Windows:</span>{" "}
              <span className="font-mono text-xs">{WINDOWS_INSTALLER_FILENAME}</span>
            </p>
            <p>
              <span className="font-semibold text-zinc-900">macOS:</span>{" "}
              <span className="font-mono text-xs">{MAC_ARM_INSTALLER_FILENAME}</span> (Apple Silicon)
            </p>
            <p>
              <span className="font-semibold text-zinc-900">Linux:</span>{" "}
              <span className="font-mono text-xs">{LINUX_INSTALLER_FILENAME}</span> (AppImage)
            </p>
            <p className="text-xs text-zinc-500 pt-1">
              Selected: <span className="font-mono">{installerFilename}</span> · Requires Google
              Chrome
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
