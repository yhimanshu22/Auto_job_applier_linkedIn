#!/usr/bin/env node
/** Minimal web assets — the desktop app loads the cloud dashboard in an external webview. */
const fs = require("fs");
const path = require("path");

const distDir = path.join(__dirname, "../dist");
const indexPath = path.join(distDir, "index.html");

if (!fs.existsSync(indexPath)) {
  fs.mkdirSync(distDir, { recursive: true });
  fs.writeFileSync(
    indexPath,
    `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>LinkdApply</title>
  </head>
  <body></body>
</html>
`,
    "utf8",
  );
  console.log(`Created ${indexPath}`);
}
