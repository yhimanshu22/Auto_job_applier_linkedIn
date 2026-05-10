/**
 * Next standalone + Turbopack can omit `.next/server` and manifests under `.next/standalone/.next`.
 * Electron bundles `frontend/.next/standalone`; without this step, `node server.js` fails at runtime.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const nextDir = path.join(root, ".next");
const stand = path.join(nextDir, "standalone");
const destNext = path.join(stand, ".next");

if (!fs.existsSync(path.join(stand, "server.js"))) {
  console.error("prepare-standalone: missing .next/standalone/server.js — run `next build` first.");
  process.exit(1);
}

fs.mkdirSync(destNext, { recursive: true });

for (const f of [
  "BUILD_ID",
  "routes-manifest.json",
  "build-manifest.json",
  "prerender-manifest.json",
  "app-path-routes-manifest.json",
  "required-server-files.json",
]) {
  const src = path.join(nextDir, f);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, path.join(destNext, f));
  }
}

const srcServer = path.join(nextDir, "server");
const destServer = path.join(destNext, "server");
if (!fs.existsSync(srcServer)) {
  console.error("prepare-standalone: missing .next/server — run `next build` first.");
  process.exit(1);
}
fs.cpSync(srcServer, destServer, { recursive: true, force: true });

// Match Docker / Next docs: static assets live under standalone/.next/static
const srcStatic = path.join(nextDir, "static");
const destStatic = path.join(destNext, "static");
if (fs.existsSync(srcStatic)) {
  fs.cpSync(srcStatic, destStatic, { recursive: true, force: true });
}

console.log("prepare-standalone: synced .next/server, BUILD_ID, manifests, and static → .next/standalone/.next");
