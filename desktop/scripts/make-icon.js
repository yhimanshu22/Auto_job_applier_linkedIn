#!/usr/bin/env node
/** Square PNG for `tauri icon` (repo icons are JPEG files named .png). */
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const assetsDir = path.join(__dirname, "../assets");
const out = path.join(assetsDir, "source-icon.png");
const src = path.join(__dirname, "../../frontend/public/icon.png");

fs.mkdirSync(assetsDir, { recursive: true });

const py = `
from PIL import Image
from pathlib import Path
img = Image.open(${JSON.stringify(src)}).convert("RGBA")
w, h = img.size
s = min(w, h)
left = (w - s) // 2
img = img.crop((left, 0, left + s, s))
img.save(${JSON.stringify(out)})
print("icon", img.size)
`;

execSync(`python -c ${JSON.stringify(py)}`, { stdio: "inherit" });
