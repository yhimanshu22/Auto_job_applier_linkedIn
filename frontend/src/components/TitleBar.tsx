"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";

export default function TitleBar() {
  const [isElectron, setIsElectron] = useState(false);

  useEffect(() => {
    // Check if running in Electron
    if (typeof window !== "undefined" && (window as any).electron) {
      setIsElectron(true);
    }
  }, []);

  if (!isElectron || (window as any).electron.isDev) return null;

  const handleMinimize = () => (window as any).electron.minimize();
  const handleMaximize = () => (window as any).electron.maximize();
  const handleClose = () => (window as any).electron.close();

  return (
    <div className="drag-region h-8 w-full bg-white dark:bg-zinc-950 border-b border-zinc-100 dark:border-zinc-900 flex items-center justify-between px-4 sticky top-0 z-[100] transition-colors">
      <div className="flex items-center gap-2 min-w-0">
        <Image
          src="/icon.png"
          alt="LinkdApply"
          width={28}
          height={28}
          className="size-7 object-contain rounded-lg shrink-0"
        />
      </div>

      <div className="no-drag flex items-center h-full">
        <button
          onClick={handleMinimize}
          className="h-full px-3 hover:bg-zinc-100 dark:hover:bg-zinc-900 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors flex items-center justify-center"
          title="Minimize"
        >
          <svg width="10" height="10" viewBox="0 0 12 12"><rect fill="currentColor" width="10" height="1" x="1" y="6"/></svg>
        </button>
        <button
          onClick={handleMaximize}
          className="h-full px-3 hover:bg-zinc-100 dark:hover:bg-zinc-900 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors flex items-center justify-center"
          title="Maximize"
        >
          <svg width="11" height="11" viewBox="0 0 12 12"><path fill="currentColor" d="M1,1V11H11V1ZM10,10H2V2H10Z"/></svg>
        </button>
        <button
          onClick={handleClose}
          className="h-full px-3 hover:bg-red-500 hover:text-white text-zinc-500 transition-colors flex items-center justify-center"
          title="Close"
        >
          <svg width="11" height="11" viewBox="0 0 12 12"><path fill="currentColor" d="M11,1.57,10.43,1,6,5.43,1.57,1,1,1.57,5.43,6,1,10.43,1.57,11,6,6.57,10.43,11,11,10.43,6.57,6Z"/></svg>
        </button>
      </div>
    </div>
  );
}
