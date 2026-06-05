# 🚀 LinkedIn AI Auto Job Applier

[Star on GitHub](https://github.com/yhimanshu22/Auto_job_applier_linkedIn/stargazers)

**Automate your job search with the power of AI.** This tool handles the tedious parts of job hunting—searching for relevant roles, answering complex application questions, and submitting applications—so you can focus on preparing for interviews.

---

## ✨ Key Features

- 🤖 **AI-Driven Applications**: Uses OpenAI, DeepSeek, or Gemini to intelligently answer application-specific questions based on your profile.
- ⚡ **Lightning Fast Search**: Automatically filters and identifies jobs that match your skills and preferences.
- 🖥️ **Premium Local Dashboard**: A sleek, modern UI built with Next.js to manage your settings, view real-time logs, and track performance in your browser.
- 🛡️ **Anti-Detection System**: Features "Safe Mode" and human-like interaction patterns to keep your LinkedIn account secure.
- 💳 **Seamless Subscriptions**: Integrated with Stripe for premium features.
- 📂 **Resume Management**: Automatically handles multiple resumes and dynamically selects the best one for each role.

---

## 🛠️ Tech Stack

- **Frontend**: Next.js 16, React 19, Tailwind CSS
- **Backend**: FastAPI (Python), Selenium, Playwright
- **AI Integration**: OpenAI, DeepSeek, Google Gemini, Anthropic Claude
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

### Manual setup (alternative)
```bash
git clone https://github.com/yhimanshu22/Auto_job_applier_linkedIn.git
cd Auto_job_applier_linkedIn/backend && pip install uv && uv sync
cd ../frontend && npm install

# Terminal 1 (backend)
cd backend && uv run uvicorn server:app --host 127.0.0.1 --port 8000

# Terminal 2 (frontend)
cd frontend && npm run dev
```

---

## ❤️ Support & Sponsorship

Building and maintaining an AI-powered automation tool requires significant resources and continuous updates to keep up with LinkedIn's platform changes. If this tool has helped you land a job or saved you time, please consider sponsoring the project!

### 🌟 Why Sponsor?
- **Faster Feature Development**: Your support allows me to dedicate more time to implementing new AI models and features.
- **Maintenance**: Helps cover the costs of testing and updating the bot to remain undetectable.
- **Priority Support**: Sponsors get priority response to issues and feature requests.

### 💰 Donation Links
- [**GitHub Sponsors**](https://github.com/sponsors/yhimanshu22) - *Preferred*
- [**Buy Me a Coffee**](https://www.buymeacoffee.com/yhimanshu22)
- [**PayPal**](https://paypal.me/yhimanshu22)

---

## 🗺️ Roadmap

- [ ] Support for more job boards (Indeed, Glassdoor).
- [ ] Advanced AI personalization based on job descriptions.
- [ ] Real-time browser view within the dashboard.
- [ ] Mobile companion app for tracking.

---

<p align="center">Made with ❤️ by <a href="https://github.com/yhimanshu22">Himanshu</a></p>
