#!/usr/bin/env node
/**
 * Build the Python sidecar with PyInstaller and copy into Tauri binaries/.
 * Skips rebuild when backend inputs are unchanged (see desktop/.cache/).
 *
 *   node scripts/build-backend.js          # use cache
 *   node scripts/build-backend.js --force  # full rebuild
 */
const crypto = require("crypto");
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const repoRoot = path.resolve(__dirname, "../..");
const backendDir = path.join(repoRoot, "backend");
const binariesDir = path.join(__dirname, "../src-tauri/binaries");
const cacheDir = path.join(__dirname, "../.cache");
const cacheFile = path.join(cacheDir, "sidecar-build.json");

const force = process.argv.includes("--force") || process.env.BUILD_SIDECAR_FORCE === "1";

const SKIP_DIRS = new Set([
  ".venv",
  "__pycache__",
  ".pytest_cache",
  "chrome_profiles",
  "dist",
  "build",
  "logs",
  "all excels",
  "node_modules",
]);

function envWithoutVirtualEnv() {
  const env = { ...process.env };
  delete env.VIRTUAL_ENV;
  return env;
}

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

function walkFiles(dir, out) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const ent of entries) {
    const full = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      if (SKIP_DIRS.has(ent.name)) continue;
      walkFiles(full, out);
      continue;
    }
    if (!ent.isFile()) continue;
    const base = ent.name;
    if (base.endsWith(".pyc") || base.endsWith(".pyo")) continue;
    out.push(full);
  }
}

/** Fingerprint backend + spec + lockfile; invalidates cache when sidecar inputs change. */
function backendSourceHash() {
  const hash = crypto.createHash("sha256");
  const files = [];

  for (const rel of ["linkdapply-backend.spec", "uv.lock", "linkdapply_backend_entry.py"]) {
    const p = path.join(backendDir, rel);
    if (fs.existsSync(p)) files.push(p);
  }

  walkFiles(backendDir, files);
  files.sort();

  for (const file of files) {
    const rel = path.relative(backendDir, file).replace(/\\/g, "/");
    hash.update(rel);
    hash.update("\0");
    hash.update(fs.readFileSync(file));
    hash.update("\0");
  }

  return hash.digest("hex");
}

function readCache() {
  try {
    return JSON.parse(fs.readFileSync(cacheFile, "utf8"));
  } catch {
    return null;
  }
}

function writeCache(payload) {
  fs.mkdirSync(cacheDir, { recursive: true });
  fs.writeFileSync(cacheFile, JSON.stringify(payload, null, 2));
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
const builtExe = path.join(backendDir, "dist", `linkdapply-backend${ext}`);
const dest = path.join(binariesDir, sidecarName);
const buildEnv = envWithoutVirtualEnv();

const inputHash = backendSourceHash();
const cached = readCache();

if (
  !force &&
  cached?.hash === inputHash &&
  cached?.triple === triple &&
  fs.existsSync(dest)
) {
  console.log(`Sidecar cache hit — skipping PyInstaller (${dest})`);
  console.log("  Use --force or npm run build:backend:force to rebuild.");
  process.exit(0);
}

stopRunningSidecar();

function cleanPyinstallerArtifacts() {
  for (const dir of [
    path.join(backendDir, "build", "linkdapply-backend"),
    path.join(backendDir, "dist", "linkdapply-backend"),
    builtExe,
  ]) {
    try {
      fs.rmSync(dir, { recursive: true, force: true, maxRetries: 8, retryDelay: 400 });
    } catch (err) {
      console.warn(`Could not remove ${dir}: ${err.message}`);
    }
  }
}

if (force) {
  console.log("Force rebuild: clearing PyInstaller output...");
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

console.log("Building backend sidecar (this may take a few minutes)...");
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
fs.copyFileSync(builtExe, dest);
if (os.platform() !== "win32") {
  fs.chmodSync(dest, 0o755);
}

writeCache({
  hash: inputHash,
  triple,
  sidecarName,
  builtAt: new Date().toISOString(),
});

console.log(`Sidecar ready: ${dest}`);
