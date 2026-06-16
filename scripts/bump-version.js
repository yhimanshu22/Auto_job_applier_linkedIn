#!/usr/bin/env node
/** Bump the repo-root VERSION file (patch by default). */
const fs = require("fs");
const path = require("path");
const { REPO_ROOT } = require("./read-version");

const kind = (process.argv[2] || "patch").toLowerCase();

function bumpVersion(current, bumpKind) {
  const match = current.match(/^(\d+)\.(\d+)\.(\d+)(-[0-9A-Za-z.]+)?$/);
  if (!match) {
    throw new Error(`Cannot bump invalid version: "${current}"`);
  }

  let major = Number(match[1]);
  let minor = Number(match[2]);
  let patch = Number(match[3]);
  const suffix = match[4] || "";

  if (bumpKind === "major") {
    major += 1;
    minor = 0;
    patch = 0;
  } else if (bumpKind === "minor") {
    minor += 1;
    patch = 0;
  } else if (bumpKind === "patch") {
    patch += 1;
  } else {
    throw new Error(`Unknown bump kind "${bumpKind}" (use patch, minor, or major)`);
  }

  return `${major}.${minor}.${patch}${suffix}`;
}

const versionPath = path.join(REPO_ROOT, "VERSION");
const current = fs.readFileSync(versionPath, "utf8").trim().split(/\r?\n/)[0].trim();
const next = bumpVersion(current, kind);
fs.writeFileSync(versionPath, `${next}\n`);

if (require.main === module) {
  process.stdout.write(next);
}

module.exports = { bumpVersion };
