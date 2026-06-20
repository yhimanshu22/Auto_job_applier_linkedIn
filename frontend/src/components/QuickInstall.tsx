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
    <section id={id} className="relative py-24 bg-zinc-950 border-t border-b border-zinc-900 scroll-mt-28 overflow-hidden">
      {/* Decorative Glow Elements */}
      <div className="absolute top-1/2 left-1/4 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none z-0" />
      <div className="absolute top-1/2 right-1/4 -translate-y-1/2 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none z-0" />

      <div className="relative mx-auto max-w-4xl px-6 lg:px-8 z-10">
        <div className="text-center space-y-4 mb-12">
          <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-white leading-tight">
            Get the <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-blue-400 to-violet-400">desktop app</span>
          </h2>
          <p className="text-zinc-400 text-lg max-w-xl mx-auto leading-relaxed">
            v{DESKTOP_VERSION} for Windows, macOS, and Linux. Install locally, configure your profile, and start applying.
          </p>
        </div>

        {/* Glassmorphic Container Card */}
        <div className="glass-card rounded-3xl border border-zinc-800/80 bg-zinc-900/40 backdrop-blur-xl p-8 lg:p-12 shadow-2xl space-y-10">
          
          {/* OS Switcher */}
          <div className="flex w-full justify-center">
            <div className="inline-flex rounded-full border border-zinc-800 bg-zinc-950/80 p-1.5 backdrop-blur">
              {OS_TABS.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setActive(t.id)}
                  className={[
                    "relative px-6 py-2.5 text-xs font-bold uppercase tracking-widest rounded-full transition-all duration-300",
                    active === t.id
                      ? "bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-lg shadow-indigo-600/20"
                      : "text-zinc-500 hover:text-zinc-200",
                  ].join(" ")}
                >
                  {t.label}
                  {detectedOs === t.id && (
                    <span className="absolute -top-1.5 -right-0.5 px-2 py-0.5 rounded-full bg-emerald-500 text-[8px] font-extrabold text-white uppercase tracking-wider scale-90 border border-zinc-950">
                      You
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Download Action Section */}
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <div className="group relative">
              {/* Pulsing button glow */}
              <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 via-blue-500 to-violet-500 rounded-full blur opacity-40 group-hover:opacity-75 transition duration-1000 group-hover:duration-200 animate-pulse"></div>
              
              <DownloadLink
                os={active}
                className="relative inline-flex items-center justify-center gap-3 px-12 py-5 text-base font-semibold text-white bg-zinc-950 rounded-full border border-zinc-800 hover:border-zinc-700 transition-all duration-300 hover:scale-[1.02] shadow-2xl"
              >
                <DownloadIcon className="w-5 h-5 text-indigo-400 group-hover:translate-y-0.5 transition-transform duration-300" />
                Download for {osLabel}
              </DownloadLink>
            </div>
            
            <p className="text-xs text-zinc-500 uppercase tracking-widest font-mono">
              Secure Local Download &bull; Free Updates Included
            </p>
          </div>

          {/* Feature Highlights Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 border-t border-zinc-800/60">
            {/* Feature 1 */}
            <div className="flex gap-4 items-start p-4 rounded-2xl bg-zinc-950/20 border border-zinc-900/40">
              <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-zinc-200">100% Secure & Local</h4>
                <p className="text-xs text-zinc-500 leading-relaxed">Your account logins and database stay securely on your own device.</p>
              </div>
            </div>

            {/* Feature 2 */}
            <div className="flex gap-4 items-start p-4 rounded-2xl bg-zinc-950/20 border border-zinc-900/40">
              <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-zinc-200">Anti-Bot Protection</h4>
                <p className="text-xs text-zinc-500 leading-relaxed">Built-in humanlike random pauses to mimic realistic browsing patterns.</p>
              </div>
            </div>

            {/* Feature 3 */}
            <div className="flex gap-4 items-start p-4 rounded-2xl bg-zinc-950/20 border border-zinc-900/40">
              <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-violet-500/10 text-violet-400 shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.213 6H16" />
                </svg>
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-semibold text-zinc-200">Automatic Updates</h4>
                <p className="text-xs text-zinc-500 leading-relaxed">Silent updates keep your application fully synchronized with LinkedIn changes.</p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
