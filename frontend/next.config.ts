import fs from "fs";
import path from "path";
import type { NextConfig } from "next";

function readRepoVersion(): string {
  try {
    const versionPath = path.join(__dirname, "..", "VERSION");
    return fs.readFileSync(versionPath, "utf8").trim().split(/\r?\n/)[0].trim();
  } catch {
    return "0.0.0";
  }
}

// In development we must allow 'unsafe-eval' for Next.js hot-reloading (React Refresh / Webpack)
// In production we can be more strict.
const isDev = process.env.NODE_ENV === "development";

const cspHeader = isDev
  ? `
    default-src 'self';
    script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:3000 http://127.0.0.1:3000 https://accounts.google.com;
    style-src 'self' 'unsafe-inline';
    img-src 'self' blob: data: https://api.producthunt.com;
    font-src 'self' data:;
    connect-src 'self' http://localhost:3000 http://127.0.0.1:3000 ws://localhost:3000 ws://127.0.0.1:3000 http://127.0.0.1:8000;
    object-src 'none';
    base-uri 'self';
    form-action 'self' http://127.0.0.1:8000 https://*.payu.in;
    frame-ancestors 'none';
  `
  : `
    default-src 'self';
    script-src 'self' 'unsafe-inline' https://accounts.google.com;
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    img-src 'self' blob: data: https:;
    font-src 'self' data: https://fonts.gstatic.com;
    frame-src 'self' https://accounts.google.com;
    object-src 'none';
    base-uri 'self';
    form-action 'self' http://127.0.0.1:8000 https://*.payu.in;
    frame-ancestors 'none';
    connect-src 'self' http://127.0.0.1:8000 https://accounts.google.com;
  `;

// The browser always calls relative /api/... URLs. In production nginx routes
// /api/ to the FastAPI backend before Next.js sees it; this rewrite covers
// local dev (and any deployment without a reverse proxy) by forwarding to the
// backend directly. Next's own routes (e.g. /api/auth/*) take precedence.
const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_DESKTOP_VERSION:
      process.env.NEXT_PUBLIC_DESKTOP_VERSION?.trim() || readRepoVersion(),
  },
  // Turbopack can mis-detect the project root on Windows in nested repos.
  turbopack: {
    root: path.join(__dirname),
  },
  webpack(config, { dev }) {
    if (dev) {
      config.output = config.output ?? {};
      config.output.chunkLoadTimeout = 120_000;
    }
    return config;
  },
  async rewrites() {
    // Use fallback so Next.js App Router handlers (e.g. /api/auth/*) win first.
    // The default array form is afterFiles and can proxy auth to FastAPI (404).
    return {
      fallback: [
        {
          source: "/api/:path*",
          destination: `${backendUrl}/api/:path*`,
        },
      ],
    };
  },
  async redirects() {
    return [
      {
        source: "/support",
        destination: "/contact",
        permanent: true,
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: cspHeader.replace(/\s{2,}/g, " ").trim(),
          },
        ],
      },
    ]
  },
};

export default nextConfig;
