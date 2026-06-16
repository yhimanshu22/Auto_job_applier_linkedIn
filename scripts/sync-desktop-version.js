#!/usr/bin/env node
/** Sync desktop package manifests from the repo-root VERSION file. */
const fs = require("fs");
const path = require("path");
const { getRepoVersion, REPO_ROOT } = require("./read-version");

const version = getRepoVersion();

function updateJsonVersion(filePath, getVersion, setVersion) {
  const raw = fs.readFileSync(filePath, "utf8");
  const data = JSON.parse(raw);
  if (getVersion(data) === version) {
    return false;
  }
  setVersion(data, version);
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`);
  return true;
}

function updateTomlVersion(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  const next = raw.replace(/^version\s*=\s*"[^"]*"/m, `version = "${version}"`);
  if (next === raw) {
    return false;
  }
  fs.writeFileSync(filePath, next);
  return true;
}

const updates = [];

if (
  updateJsonVersion(
    path.join(REPO_ROOT, "desktop", "package.json"),
    (data) => data.version,
    (data, value) => {
      data.version = value;
    },
  )
) {
  updates.push("desktop/package.json");
}

if (
  updateJsonVersion(
    path.join(REPO_ROOT, "desktop", "src-tauri", "tauri.conf.json"),
    (data) => data.version,
    (data, value) => {
      data.version = value;
    },
  )
) {
  updates.push("desktop/src-tauri/tauri.conf.json");
}

if (updateTomlVersion(path.join(REPO_ROOT, "desktop", "src-tauri", "Cargo.toml"))) {
  updates.push("desktop/src-tauri/Cargo.toml");
}

if (updates.length > 0) {
  console.log(`Synced ${version} -> ${updates.join(", ")}`);
} else {
  console.log(`Desktop manifests already at ${version}`);
}
