# 🚀 LinkedIn AI Auto Job Applier

[Star on GitHub](https://github.com/yhimanshu22/Auto_job_applier_linkedIn/stargazers)

**Automate your job search with the power of AI.** This tool handles the tedious parts of job hunting—searching for relevant roles, answering complex application questions, submitting applications, and running LinkedIn engagement workflows—so you can focus on preparing for interviews.

---

## Table of Contents

- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Run the Job Application Bot](#-run-the-job-application-bot)
- [LinkedIn Automation](#-linkedin-automation)
- [Troubleshooting](#-troubleshooting)
- [Support & Sponsorship](#-support--sponsorship)
- [Roadmap](#-roadmap)

---

## ✨ Key Features

- 🤖 **AI-Driven Applications**: Uses OpenAI, DeepSeek, or Gemini to intelligently answer application-specific questions based on your profile.
- ⚡ **Lightning Fast Search**: Automatically filters and identifies jobs that match your skills and preferences.
- 🖥️ **Premium Local Dashboard**: A sleek Next.js UI to manage settings, view real-time logs, track applications, and run automation tasks in your browser.
- 📣 **LinkedIn Automation**: Post, engage, pursue profiles, and generate content calendars via the dashboard or CLI.
- 🛡️ **Anti-Detection System**: Human-like interaction patterns and safe-mode options to reduce bot-like timing.
- 💳 **Seamless Subscriptions**: Integrated with Stripe for premium features.
- 📂 **Resume Management**: Handles multiple resumes and selects the best one per role.

---

## 🛠️ Tech Stack

- **Frontend**: Next.js 16, React 19, Tailwind CSS
- **Backend**: FastAPI (Python), Selenium, undetected-chromedriver
- **AI**: OpenAI, DeepSeek, Google Gemini, Groq (OpenAI-compatible)
- **Database**: SQLite
- **Payments**: Stripe

---

## 🚀 Quick Start

### One-command install

**macOS / Linux**
```bash
curl -fsSL "https://raw.githubusercontent.com/yhimanshu22/Auto_job_applier_linkedIn/main/install.sh" | bash
```

**Windows (PowerShell)**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr -useb 'https://raw.githubusercontent.com/yhimanshu22/Auto_job_applier_linkedIn/main/install.ps1' | iex"
```

This clones the repo, installs dependencies, creates `.env` templates, and starts the backend (`http://127.0.0.1:8000`) and dashboard (`http://localhost:3000`).

### Prerequisites

- Git
- Python 3.10+
- Node.js & npm
- Google Chrome

### Manual setup

```bash
git clone https://github.com/yhimanshu22/Auto_job_applier_linkedIn.git
cd Auto_job_applier_linkedIn/backend && pip install uv && uv sync
cd ../frontend && npm install

# Terminal 1 (backend)
cd backend && uv run uvicorn server:app --host 127.0.0.1 --port 8000

# Terminal 2 (frontend)
cd frontend && npm run dev
```

Open **http://localhost:3000** for the dashboard and **http://127.0.0.1:8000** for the API.

### Desktop app (Tauri thin launcher)

For end users who should not clone the repo: the `desktop/` app starts the **local bot sidecar** and opens your **hosted dashboard** (Vercel) for login and billing. See [desktop/README.md](desktop/README.md).

```bash
cd desktop && npm install && npm run icon
cp .env.example .env   # set LINKDAPPLY_FRONTEND_URL to your Vercel URL
npm run dev            # requires Rust: https://rustup.rs/
```

---

## ⚙️ Configuration

### Dashboard (recommended)

1. Start backend and frontend (see [Quick Start](#-quick-start)).
2. Open `http://localhost:3000` and sign in.
3. Use the dashboard to set personal details, job-search filters, question answers, secrets (API keys), and LinkedIn accounts.

Settings are stored in SQLite and loaded at runtime via `backend/config/config_bridge.py`.

### Environment variables

Create `backend/.env` for secrets and credentials (see `backend/linkedin_automation/.env.example` for automation-related keys):

```ini
LINKEDIN_USERNAME=you@example.com
LINKEDIN_PASSWORD=your_password

# Job-bot AI (OpenAI-compatible — works with Groq)
AI_PROVIDER=openai
LLM_API_URL=https://api.groq.com/openai/v1/
LLM_API_KEY=your_key
LLM_MODEL=llama-3.3-70b-versatile

# LinkedIn automation AI (optional overrides)
LINKEDIN_AI_PROVIDER=groq
OPENAI_API_KEY=
GEMINI_API_KEY=
```

Multi-account bots: use `LINKEDIN_USERNAME_1` / `LINKEDIN_PASSWORD_1`, `_2`, etc.

### Chrome / drivers

On Windows, `undetected-chromedriver` usually resolves Chrome automatically. If you see session errors, close all Chrome windows and retry, or enable safe mode in dashboard settings.

---

## ▶️ Run the Job Application Bot

The Easy Apply bot searches LinkedIn and submits applications using your configured profile and AI answers.

### From the dashboard

1. Configure search filters and secrets in the UI.
2. Go to the main dashboard and click **Start Bot**.
3. Use **Stop Bot** before shutting down the backend — the supervisor runs as a background process and is not stopped when you Ctrl+C uvicorn.

### From the CLI

```bash
cd backend
uv run python runAiBot.py
```

**Important:** Close all other Chrome windows before starting the bot.

---

## 📣 LinkedIn Automation

The `backend/linkedin_automation` package handles posting, feed engagement, profile pursuit, and content-calendar generation. Use it from the **Automation** tab in the dashboard (`/dashboard/automation`) or from the CLI.

### Features

| Capability | Description |
|------------|-------------|
| **Post** | Publish text posts with optional images and scheduling |
| **Engage** | Scroll the feed, like and comment with AI-generated replies |
| **Pursue** | Search a profile, follow, and engage with their posts |
| **Calendar** | Generate a multi-day content plan (`generate-calendar`) |
| **Mentions** | Tag people with `@{Name}` or `--mention-author` |
| **De-duplication** | Skips posts already liked/commented (URN + text hash cache) |

### Dashboard

1. Open `http://localhost:3000/dashboard/automation`.
2. Choose an account, tab (Post / Engage / Pursue / Calendar / Settings), and configure options.
3. Start a task and watch logs in the UI.

### CLI (advanced)

From `backend/`:

```bash
# Help
uv run python -m linkedin_automation --help

# Post plain text
uv run python -m linkedin_automation post --post-text "Hello LinkedIn!" --no-ai --debug

# Engage with feed (like + comment)
uv run python -m linkedin_automation engage --action both --max-actions 5 --debug

# Pursue a profile
uv run python -m linkedin_automation pursue "Jane Doe" --max-posts 3 --debug

# Generate content calendar
uv run python -m linkedin_automation generate-calendar --niche "tech careers" --total-posts 30
```

Use `--headless=false` on first runs to watch the browser. Logs are written under `backend/logs/`.

### Automation safety

- Use conservative delays (`--delay-min` / `--delay-max`) and daily limits.
- Start with `--headless=false --debug` until behaviour looks correct.
- Engage de-dupe state is stored in `logs/engage_state.json` (delete to reset).
- Follow LinkedIn's terms; automation carries account risk.

### Package layout

```
backend/linkedin_automation/
├── __main__.py           # CLI entry (python -m linkedin_automation)
├── linkedin_bot.py       # High-level orchestrator
├── config.py             # Env-based configuration
├── openai_client.py      # Multi-provider LLM helpers
├── linkedin_ui/          # Selenium UI modules (login, engage, composer, …)
├── topics.txt            # Default post topics
└── content_calendar.txt  # Sample calendar output
```

---

## ❓ Troubleshooting

### Chrome / session errors

- **Cause**: Chrome already open, version mismatch, or headless feed issues.
- **Fix**: Close all Chrome windows, restart the bot, run with `--headless=false`, or enable safe mode in settings.

### Bot keeps running after stopping backend

The job supervisor is a **separate background process**. Always click **Stop Bot** in the dashboard (or `POST /api/bot/stop`) before killing uvicorn.

### AI / API errors

- Verify API keys in the dashboard **Secrets** tab or `backend/.env`.
- For Groq: set `AI_PROVIDER=openai` and `LLM_API_URL` to the Groq OpenAI endpoint.
- Check quota/rate limits in provider dashboards.

### `uv` virtualenv warning

If you see a `VIRTUAL_ENV` mismatch warning, run `deactivate` (or clear `VIRTUAL_ENV`) before `uv run` from `backend/`, so uv uses `backend/.venv` instead of a repo-root `.venv`.

### Automation duplicates or skips

Run engage with `--debug` and inspect `backend/logs/` for `ENGAGE_SKIP` lines. Reset cache by deleting `logs/engage_state.json`.

---

## ❤️ Support & Sponsorship

Building and maintaining an AI-powered automation tool requires significant resources and continuous updates to keep up with LinkedIn's platform changes. If this tool has helped you land a job or saved you time, please consider sponsoring the project!

### 🌟 Why Sponsor?

- **Faster Feature Development**: Your support allows more time for new AI models and features.
- **Maintenance**: Covers testing and updates to remain reliable on LinkedIn.
- **Priority Support**: Sponsors get priority response to issues and feature requests.

### 💰 Donation Links

- [**GitHub Sponsors**](https://github.com/sponsors/yhimanshu22) — *Preferred*
- [**Buy Me a Coffee**](https://www.buymeacoffee.com/yhimanshu22)
- [**PayPal**](https://paypal.me/yhimanshu22)

---

## 🗺️ Roadmap

- [ ] Support for more job boards (Indeed, Glassdoor)
- [ ] Advanced AI personalization based on job descriptions
- [ ] Real-time browser view within the dashboard
- [ ] Mobile companion app for tracking

---

**Disclaimer**: This tool is for educational purposes. Use it responsibly and at your own risk. Be aware of LinkedIn's terms of service regarding automation.

<p align="center">Made with ❤️ by <a href="https://github.com/yhimanshu22">Himanshu</a></p>
