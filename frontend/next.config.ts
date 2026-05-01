import type { NextConfig } from "next";

// In development we must allow 'unsafe-eval' for Next.js hot-reloading (React Refresh / Webpack)
// In production we can be more strict.
const isDev = process.env.NODE_ENV === "development";

const cspHeader = isDev
  ? `
    default-src 'self';
    script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:3000;
    style-src 'self' 'unsafe-inline';
    img-src 'self' blob: data:;
    font-src 'self' data:;
    connect-src 'self' http://localhost:3000 ws://localhost:3000 http://127.0.0.1:8000;
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
  `
  : `
    default-src 'self';
    script-src 'self';
    style-src 'self' 'unsafe-inline';
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    connect-src 'self' http://127.0.0.1:8000;
  `;

const nextConfig: NextConfig = {
  output: "standalone",
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
