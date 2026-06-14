# LinkdApply Desktop (Tauri thin launcher)

Runs the **local Python backend** (bot + Chrome) and opens the dashboard in a desktop window.

## Local dev (start here)

Everything runs on your machine — no AWS required.

**Terminal 1 — frontend**

```bash
cd frontend && npm install && npm run dev
```

**Terminal 2 — desktop app** (starts the backend sidecar automatically)

```bash
cd desktop
cp .env.example .env   # first time only; already points at localhost:3000
npm install
npm run dev
```

Do **not** run `uvicorn` manually in a third terminal unless you stop Tauri first — both bind port `8000`.

| What | Local URL |
|------|-----------|
| Dashboard (browser) | http://localhost:3000 |
| Dashboard (Tauri) | http://localhost:3000/dashboard?desktop=1 |
| Bot / config API | http://127.0.0.1:8000 |

Optional: open http://localhost:3000 in Chrome instead of Tauri — bot still uses the local backend via Next.js rewrites.

## Architecture

| Data | Where |
|------|--------|
| Configs, secrets, LinkedIn creds, applications, bot logs | **Local SQLite** (`%LOCALAPPDATA%\LinkdApply\data.db`) |
| Subscriptions, Stripe/PayU | Local backend SQLite in dev; cloud AWS + Render Postgres in production |
| Dashboard UI, login | Local `npm run dev` in dev; hosted AWS frontend in production |

The sidecar sets `LINKDAPPLY_LOCAL_DATA=true` so user configs never go to Render Postgres.

| API call (desktop app) | Target (local dev) |
|------------------------|---------------------|
| `/api/config/*`, `/api/bot/*`, secrets, uploads | Local `127.0.0.1:8000` |
| `/api/billing/*` | Next.js on `:3000` → local backend |

In production, set `CLOUD_API_URL` + `LINKDAPPLY_INTERNAL_KEY` so bot start can verify subscription against AWS.

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

# 3. Local dev config (default)
cp .env.example .env
# LINKDAPPLY_FRONTEND_URL=http://localhost:3000/dashboard?desktop=1 — no cloud vars needed

# 4. Optional local sidecar overrides (packaged installs)
# Copy desktop/templates/user.env.example → %LOCALAPPDATA%\LinkdApply\.env
# Do NOT set DATABASE_URL there — configs stay local SQLite.
```

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
| `SEC_E_DECRYPT_FAILURE` / `curl failed` on `cargo fetch` | Network/TLS issue downloading Rust crates (not app code). Try: (1) run again, (2) turn off VPN, (3) use phone hotspot, (4) `cd desktop/src-tauri && cargo fetch`, then `npm run dev`. Project includes `.cargo/config.toml` with Windows schannel workarounds. |
| “Backend did not become healthy” | Ensure `uv` is on PATH; free port 8000 (`netstat -ano | findstr :8000` on Windows); run `unset VIRTUAL_ENV` if another project's venv is active; try `cd backend && uv run python -m uvicorn server:app --host 127.0.0.1 --port 8000` manually |
| “Your connection is not private” in Tauri | `desktop/.env` must use `http://localhost:3000`, not `https://app.yourdomain.com` |
| Bot Start fails from desktop | Confirm `?desktop=1` in URL; check browser devtools for blocked calls to `:8000` |
| Login works but bot 402 | Set `CLOUD_API_URL` + matching `LINKDAPPLY_INTERNAL_KEY` on desktop and AWS |
| Release build missing sidecar | Run `npm run build:backend` before `npm run build` |
