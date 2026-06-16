"use client";

import { useEffect, useState } from "react";
import DownloadLink, { DownloadIcon } from "@/components/DownloadLink";
import {
  DESKTOP_VERSION,
  detectInstallOs,
  getOsLabel,
  type InstallOs,
} from "@/lib/install";

type QuickInstallProps = {
  id?: string;
};

const OS_TABS = [
  { id: "windows", label: "Windows" },
  { id: "mac", label: "macOS" },
  { id: "linux", label: "Linux" },
] as const;

const SSR_DEFAULT_OS: InstallOs = "windows";

export default function QuickInstall({ id = "install" }: QuickInstallProps) {
  const [active, setActive] = useState<InstallOs>(SSR_DEFAULT_OS);
  const [detectedOs, setDetectedOs] = useState<InstallOs | null>(null);

  useEffect(() => {
    const os = detectInstallOs();
    setActive(os);
    setDetectedOs(os);
  }, []);

  const osLabel = getOsLabel(active);

  return (
    <section id={id} className="py-24 bg-white border-y border-zinc-100 scroll-mt-28">
      <div className="mx-auto max-w-3xl px-6 lg:px-8">
        <div className="text-center space-y-3 mb-8">
          <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900 leading-tight">
            Get the <span className="text-accent italic">desktop app</span>
          </h2>
          <p className="text-zinc-500">
            v{DESKTOP_VERSION} for Windows, macOS, and Linux. Install, sign in, and start applying.
          </p>
        </div>

        <div className="rounded-3xl border border-zinc-200 bg-zinc-50 p-6 lg:p-8 shadow-sm space-y-6">
          <div className="flex w-full justify-center">
            <div className="inline-flex rounded-full border border-zinc-200 bg-white p-1">
            {OS_TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setActive(t.id)}
                className={[
                  "relative px-4 py-2 text-xs font-bold uppercase tracking-widest rounded-full transition-colors",
                  active === t.id
                    ? "bg-zinc-900 text-white"
                    : "text-zinc-600 hover:text-zinc-900",
                ].join(" ")}
              >
                {t.label}
                {detectedOs === t.id && (
                  <span className="absolute -top-2 -right-1 px-1.5 py-0.5 rounded-full bg-accent text-[8px] font-bold text-white uppercase tracking-wide">
                    You
                  </span>
                )}
              </button>
            ))}
            </div>
          </div>

          <div className="flex flex-col items-center text-center">
            <DownloadLink
              os={active}
              className="inline-flex items-center justify-center gap-2 rounded-xl px-8 py-3.5 text-sm font-semibold text-white purple-gradient-button shadow-md hover:scale-[1.02] transition-all"
            >
              <DownloadIcon />
              Download for {osLabel}
            </DownloadLink>
          </div>
        </div>
      </div>
    </section>
  );
}
