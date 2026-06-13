#!/usr/bin/env node
/**
 * Build the Python sidecar with PyInstaller and copy into Tauri binaries/.
 * Requires: uv, Rust target toolchain, PyInstaller (installed via uv pip).
 */
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const repoRoot = path.resolve(__dirname, "../..");
const backendDir = path.join(repoRoot, "backend");
const binariesDir = path.join(__dirname, "../src-tauri/binaries");

const triple = execSync("rustc -vV", { encoding: "utf8" })
  .split("\n")
  .find((l) => l.startsWith("host:"))
  ?.split("host:")[1]
  ?.trim();

if (!triple) {
  console.error("Could not detect Rust host triple. Install Rust first.");
  process.exit(1);
}

const ext = os.platform() === "win32" ? ".exe" : "";
const sidecarName = `linkdapply-backend-${triple}${ext}`;
const builtExe = path.join(backendDir, "dist", "linkdapply-backend", `linkdapply-backend${ext}`);

console.log("Installing PyInstaller...");
execSync("uv pip install pyinstaller", { cwd: backendDir, stdio: "inherit" });

console.log("Building backend sidecar...");
execSync("uv run pyinstaller linkdapply-backend.spec --noconfirm --clean", {
  cwd: backendDir,
  stdio: "inherit",
});

if (!fs.existsSync(builtExe)) {
  console.error(`Expected build output at ${builtExe}`);
  process.exit(1);
}

fs.mkdirSync(binariesDir, { recursive: true });
const dest = path.join(binariesDir, sidecarName);
fs.copyFileSync(builtExe, dest);
if (os.platform() !== "win32") {
  fs.chmodSync(dest, 0o755);
}

console.log(`Sidecar ready: ${dest}`);
