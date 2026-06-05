"use client";

import { useEffect, useMemo, useState } from "react";
import {
  detectInstallOs,
  getInstallCommand,
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

// Stable default for SSR + first client paint; real OS is applied after mount.
const SSR_DEFAULT_OS: InstallOs = "windows";

export default function QuickInstall({ id, variant = "section" }: QuickInstallProps) {
  const [active, setActive] = useState<InstallOs>(SSR_DEFAULT_OS);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setActive(detectInstallOs());
  }, []);

  const command = useMemo(() => getInstallCommand(active), [active]);

  async function onCopy() {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      // ignore: clipboard may be blocked; user can copy manually
    }
  }

  if (variant === "compact") {
    return (
      <div className="w-full max-w-2xl mx-auto space-y-3 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-500">
        <div className="inline-flex rounded-full border border-zinc-200 bg-white p-1 mx-auto">
          {OS_TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setActive(t.id)}
              className={[
                "px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded-full transition-colors",
                active === t.id
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-600 hover:text-zinc-900",
              ].join(" ")}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-3 shadow-sm">
          <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
            <pre className="flex-1 overflow-x-auto rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-left text-xs text-zinc-800 leading-relaxed">
              <code>{command}</code>
            </pre>
            <button
              type="button"
              onClick={onCopy}
              className="shrink-0 inline-flex items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white purple-gradient-button shadow-md hover:scale-[1.02] transition-all"
            >
              {copied ? "Copied" : "Copy command"}
            </button>
          </div>
        </div>

        <p className="text-xs text-zinc-500 text-center">
          Requires Git, Python 3.10+, Node.js, and Google Chrome. Opens dashboard at{" "}
          <span className="font-semibold text-zinc-700">http://localhost:3000</span>
        </p>
      </div>
    );
  }

  return (
    <section id={id} className="py-24 bg-white border-y border-zinc-100 scroll-mt-28">
      <div className="mx-auto max-w-4xl px-6 lg:px-8">
        <div className="text-center space-y-4 mb-10">
          <h2 className="font-serif text-4xl lg:text-5xl font-medium tracking-tight text-zinc-900 leading-tight">
            Install in <span className="text-accent italic">one command</span>
          </h2>
          <p className="text-zinc-500">
            Copy, paste, run. This installs dependencies, sets up the app, then starts the backend and dashboard.
          </p>
        </div>

        <div className="rounded-3xl border border-zinc-200 bg-zinc-50 p-6 lg:p-8 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
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

            <button
              type="button"
              onClick={onCopy}
              className="inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold text-white purple-gradient-button shadow-md hover:scale-[1.02] transition-all"
            >
              {copied ? "Copied" : "Copy command"}
            </button>
          </div>

          <pre className="overflow-x-auto rounded-2xl border border-zinc-200 bg-white p-4 text-sm text-zinc-800 leading-relaxed">
            <code>{command}</code>
          </pre>

          <div className="mt-5 text-xs text-zinc-500 space-y-1">
            <p>
              Backend: <span className="font-semibold text-zinc-700">http://127.0.0.1:8000</span> · Dashboard:{" "}
              <span className="font-semibold text-zinc-700">http://localhost:3000</span>
            </p>
            <p>
              Requires Git, Python 3.10+, Node.js, and Google Chrome.
            </p>
            <p>
              After first run, fill credentials in <span className="font-mono">backend/.env</span> (it’s created automatically).
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
