# LinkdApply Desktop (Tauri thin launcher)

Runs the **local Python backend** (bot + Chrome) and opens your **hosted dashboard** for login, billing, and settings.

## Architecture

| Data | Where |
|------|--------|
| Configs, secrets, LinkedIn creds, applications, bot logs | **Local SQLite** (`%LOCALAPPDATA%\LinkdApply\data.db`) |
| Subscriptions, Stripe/PayU | **Cloud AWS API** + Render Postgres |
| Dashboard UI, login | **Hosted AWS frontend** |

The sidecar sets `LINKDAPPLY_LOCAL_DATA=true` so user configs never go to Render Postgres.

| API call (desktop app) | Target |
|------------------------|--------|
| `/api/config/*`, `/api/bot/*`, secrets, uploads | Local `127.0.0.1:8000` |
| `/api/billing/*` | Cloud AWS API |

Bot start verifies subscription via `CLOUD_API_URL` + `LINKDAPPLY_INTERNAL_KEY`.

## Prerequisites

- [Rust](https://rustup.rs/)
- [Node.js](https://nodejs.org/) 20+
- [uv](https://docs.astral.sh/uv/) + Python 3.10+ (backend)
- Google Chrome (for the bot)

## First-time setup

```bash
# 1. Backend deps
cd backend && uv sync

# 2. Desktop deps + icons
cd ../desktop
npm install
npm run icon

# 3. Configure hosted dashboard URL
cp .env.example .env
# Edit .env — set LINKDAPPLY_FRONTEND_URL, CLOUD_API_URL, LINKDAPPLY_INTERNAL_KEY

# 4. Optional local sidecar overrides (packaged installs)
# Copy desktop/templates/user.env.example → %LOCALAPPDATA%\LinkdApply\.env
# Do NOT set DATABASE_URL there — configs stay local SQLite.
```

## Development

Terminal 1 — hosted frontend (or use your deployed Vercel URL in `.env`):

```bash
cd frontend && npm run dev
```

Terminal 2 — desktop launcher (spawns `uv run uvicorn` automatically):

```bash
cd desktop
# Optional: load .env into the shell
export LINKDAPPLY_FRONTEND_URL=http://localhost:3000/dashboard?desktop=1  # Git Bash
npm run dev
```

The app waits for `http://127.0.0.1:8000/api/health`, then opens the dashboard webview.

## Production build

```bash
cd desktop
npm run build:backend   # PyInstaller → src-tauri/binaries/linkdapply-backend-<triple>
npm run build           # Tauri installer (.msi / .dmg / .AppImage)
```

Install output: `desktop/src-tauri/target/release/bundle/`

### End-user config

After install, create:

**Windows:** `%LOCALAPPDATA%\LinkdApply\.env`

```ini
ENCRYPTION_KEY=same-as-aws
CLOUD_API_URL=https://api.yourdomain.com
LINKDAPPLY_INTERNAL_KEY=same-shared-secret
FRONTEND_URL=https://app.yourdomain.com
EXTRA_CORS_ORIGINS=https://app.yourdomain.com
```

User data (local SQLite `data.db`, logs, Chrome profiles) lives under `%LOCALAPPDATA%\LinkdApply\`.

## AWS checklist

1. Deploy frontend on AWS with `BACKEND_URL=https://api.yourdomain.com`
2. Deploy FastAPI on AWS with Render Postgres (`DATABASE_URL`) — **subscriptions only**; configs are not stored here for desktop users
3. Set on **AWS backend**: `LINKDAPPLY_INTERNAL_KEY`, `REQUIRE_AUTH=true`
4. Set on **desktop `.env`**: same `LINKDAPPLY_INTERNAL_KEY`, `CLOUD_API_URL`
5. Local sidecar `.env`: `FRONTEND_URL` + `EXTRA_CORS_ORIGINS` for CORS
6. Production CSP already allows `connect-src http://127.0.0.1:8000` in `frontend/next.config.ts`

## Troubleshooting

| Issue | Fix |
|-------|-----|
| “Backend did not become healthy” | Ensure `uv` is on PATH; try `cd backend && uv run uvicorn server:app` manually |
| Bot Start fails from desktop | Confirm `?desktop=1` in URL; check browser devtools for blocked calls to `:8000` |
| Login works but bot 402 | Set `CLOUD_API_URL` + matching `LINKDAPPLY_INTERNAL_KEY` on desktop and AWS |
| Release build missing sidecar | Run `npm run build:backend` before `npm run build` |
