"use client";

import {
  getDesktopDownloadUrl,
  getInstallerFilename,
  getOsLabel,
  type InstallOs,
} from "@/lib/install";

type DownloadLinkProps = {
  os?: InstallOs;
  className?: string;
  children: React.ReactNode;
  download?: boolean;
};

function DownloadIcon() {
  return (
    <svg
      className="size-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

export default function DownloadLink({
  os = "windows",
  className = "",
  children,
  download = true,
}: DownloadLinkProps) {
  const url = getDesktopDownloadUrl(os);
  const filename = getInstallerFilename(os);

  return (
    <a
      href={url}
      download={download ? filename : undefined}
      className={className}
    >
      {children}
    </a>
  );
}

export { DownloadIcon };

export function DownloadForOsButton({
  os,
  className,
  label,
}: {
  os: InstallOs;
  className: string;
  label?: string;
}) {
  return (
    <DownloadLink os={os} className={className}>
      <DownloadIcon />
      {label ?? `Download for ${getOsLabel(os)}`}
    </DownloadLink>
  );
}
