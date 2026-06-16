"use client";

import DownloadLink, { DownloadIcon } from "@/components/DownloadLink";
import { detectInstallOs, getOsLabel } from "@/lib/install";
import { useEffect, useState } from "react";
import type { InstallOs } from "@/lib/install";

export default function HeroDownloadButton() {
  const [os, setOs] = useState<InstallOs>("windows");

  useEffect(() => {
    setOs(detectInstallOs());
  }, []);

  return (
    <DownloadLink
      os={os}
      className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 px-10 py-4 text-white font-semibold shadow-xl transition-all hover:bg-zinc-800 hover:scale-[1.02]"
    >
      <DownloadIcon />
      Download for {getOsLabel(os)}
    </DownloadLink>
  );
}
