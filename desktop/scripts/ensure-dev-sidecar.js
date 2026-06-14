#!/usr/bin/env node
/** Create a tiny stub sidecar exe so `tauri dev` can compile before PyInstaller build. */
const { execSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const triple = execSync("rustc -vV", { encoding: "utf8" })
  .split("\n")
  .find((l) => l.startsWith("host:"))
  ?.split("host:")[1]
  ?.trim();

if (!triple) {
  console.error("rustc not found");
  process.exit(1);
}

const ext = os.platform() === "win32" ? ".exe" : "";
const binariesDir = path.join(__dirname, "../src-tauri/binaries");
const dest = path.join(binariesDir, `linkdapply-backend-${triple}${ext}`);

if (fs.existsSync(dest)) {
  console.log(`Dev sidecar present: ${dest}`);
  process.exit(0);
}

fs.mkdirSync(binariesDir, { recursive: true });
const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "linkdapply-stub-"));
const src = path.join(tmpDir, "main.rs");
fs.writeFileSync(src, "fn main() {}\n");

console.log(`Creating dev sidecar stub: ${dest}`);
execSync(`rustc "${src}" -o "${dest}"`, { stdio: "inherit" });
if (os.platform() !== "win32") {
  fs.chmodSync(dest, 0o755);
}
