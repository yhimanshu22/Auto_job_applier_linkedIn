#!/usr/bin/env node
/**
 * Build the Python sidecar with PyInstaller and copy into Tauri binaries/.
 * Requires: uv, Rust target toolchain.
 */
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const repoRoot = path.resolve(__dirname, "../..");
const backendDir = path.join(repoRoot, "backend");
const binariesDir = path.join(__dirname, "../src-tauri/binaries");

function envWithoutVirtualEnv() {
  const env = { ...process.env };
  delete env.VIRTUAL_ENV;
  return env;
}

/** Stop desktop/sidecar processes that lock backend/.venv on Windows. */
function stopRunningSidecar() {
  if (os.platform() !== "win32") return;

  console.log("Stopping running LinkdApply backend (if any)...");

  for (const image of ["linkdapply-backend.exe", "linkdapply-desktop.exe"]) {
    try {
      execSync(`cmd.exe /c taskkill /F /IM ${image} /T`, { stdio: "ignore" });
    } catch {
      /* not running */
    }
  }

  try {
    execSync(
      'powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \\"name=\'python.exe\'\\" | Where-Object { $_.CommandLine -match \'linkdapply\\\\backend\\\\.venv\' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"',
      { stdio: "ignore" }
    );
  } catch {
    /* none */
  }

  try {
    execSync(
      'powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"',
      { stdio: "ignore" }
    );
  } catch {
    /* none */
  }
}

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
// Onefile PyInstaller output (self-contained; required for MSI externalBin).
const builtExe = path.join(backendDir, "dist", `linkdapply-backend${ext}`);

const buildEnv = envWithoutVirtualEnv();

stopRunningSidecar();

function cleanPyinstallerArtifacts() {
  for (const dir of [
    path.join(backendDir, "build", "linkdapply-backend"),
    path.join(backendDir, "dist", "linkdapply-backend"),
    path.join(backendDir, "dist", `linkdapply-backend${ext}`),
  ]) {
    try {
      fs.rmSync(dir, { recursive: true, force: true, maxRetries: 8, retryDelay: 400 });
    } catch (err) {
      console.warn(`Could not remove ${dir}: ${err.message}`);
    }
  }
}

cleanPyinstallerArtifacts();

console.log("Installing PyInstaller into backend venv...");
try {
  execSync("uv pip install pyinstaller", {
    cwd: backendDir,
    stdio: "inherit",
    env: buildEnv,
  });
} catch (err) {
  console.error(
    "\nCould not update backend/.venv. Close LinkdApply and any terminal running uvicorn, then retry."
  );
  throw err;
}

console.log("Building backend sidecar...");
try {
  execSync("uv run pyinstaller linkdapply-backend.spec --noconfirm", {
    cwd: backendDir,
    stdio: "inherit",
    env: buildEnv,
  });
} catch (err) {
  console.error(
    "\nBuild failed. Close LinkdApply / any backend on port 8000, then retry."
  );
  throw err;
}

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
