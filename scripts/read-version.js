#!/usr/bin/env node
/** Read the canonical app version from the repo-root VERSION file. */
const fs = require("fs");
const path = require("path");

const REPO_ROOT = path.join(__dirname, "..");

function getRepoVersion() {
  const versionFile = path.join(REPO_ROOT, "VERSION");
  if (!fs.existsSync(versionFile)) {
    throw new Error(`Missing VERSION file at ${versionFile}`);
  }

  const line = fs.readFileSync(versionFile, "utf8").trim().split(/\r?\n/)[0].trim();
  if (!line || !/^\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?$/.test(line)) {
    throw new Error(`Invalid VERSION file contents: "${line}"`);
  }

  return line;
}

if (require.main === module) {
  process.stdout.write(getRepoVersion());
}

module.exports = { getRepoVersion, REPO_ROOT };
