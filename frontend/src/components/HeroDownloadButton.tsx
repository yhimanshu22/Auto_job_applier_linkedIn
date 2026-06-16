"use client";

import { DownloadForOsButton } from "@/components/DownloadLink";
import { detectInstallOs } from "@/lib/install";
import { useEffect, useState } from "react";
import type { InstallOs } from "@/lib/install";

export default function HeroDownloadButton() {
  const [os, setOs] = useState<InstallOs>("windows");

  useEffect(() => {
    setOs(detectInstallOs());
  }, []);

  return (
    <DownloadForOsButton
      os={os}
      className="btn-on-light w-full sm:w-auto inline-flex items-center justify-center gap-2 px-10 py-4 font-semibold shadow-xl transition-all hover:scale-[1.02]"
    />
  );
}
