# LinkedIn AI Auto Job Applier

Welcome! This bot automates the process of applying to jobs on LinkedIn. It searches for relevant jobs, answers application questions using AI, and submits applications for you—saving you hours of manual work.

---

## 🚀 Quick Start Guide

Follow these steps to get the bot running in minutes!

### 1. Prerequisites
*   **Python 3.10+**: [Download Here](https://www.python.org/downloads/) (Make sure to check "Add Python to PATH" during installation).
*   **Google Chrome**: [Download Here](https://www.google.com/chrome).

### 2. Installation

You can set up the project using either `uv` (recommended) or standard `pip`.

#### Option A: Using `uv` (Recommended)
`uv` is a strictly faster Python package installer and resolver.

1.  **Install uv** (if not already installed):
    ```bash
    pip install uv
    ```
2.  **Install Dependencies**:
    ```bash
    uv sync
    # OR if you just want to install requirements directly
    uv pip install -r requirements.txt
    ```

#### Option B: Using standard `pip`
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Setup Drivers
*   **Windows**: Double-click `setup/windows-setup.bat` to automatically download the correct ChromeDriver.

---

## ⚙️ Configuration

The easiest way to configure the bot is using the built-in UI.

### Method 1: Visual Configuration (Recommended)
Run the configuration UI to easily edit your personal details, answers, and search preferences.

```bash
# If using uv
uv run streamlit run config_ui.py

# If using standard python
streamlit run config_ui.py
```

This will open a web interface where you can set:
*   **Personal Info**: Name, contact details, etc.
*   **Questions**: Standard answers for experience, visa status, etc.
*   **Search**: Job titles, locations, and filters.
*   **Settings**: Bot behavior like stealth mode and AI providers.
*   **Secrets**: API keys and credentials (saved to `.env`).

### Method 2: Manual Configuration
You can also manually edit the files in the `config/` folder:
*   `config/personals.py`
*   `config/questions.py`
*   `config/search.py`
*   `config/settings.py`
*   `.env` for secrets (create looking at `config/secrets.py` as reference)

---

## ▶️ Run the Bot

1.  **Close all existing Google Chrome windows.** (Important!)
2.  Run the command:

    **Using `uv`:**
    ```bash
    uv run runAiBot.py
    ```

    **Using standard Python:**
    ```bash
    python runAiBot.py
    ```

3.  Sit back and watch it apply!

---

## ❓ Troubleshooting

### "Session not created" or "Chrome not connecting"
*   **Cause**: Chrome is likely already running or there is a version mismatch.
*   **Fix**:
    1.  **Close ALL Chrome windows** and try again.
    2.  If that fails, set `safe_mode = True` in `config/settings.py` (or via the UI).
    3.  Check if your Chrome browser updated recently. You may need to re-run `setup/windows-setup.bat`.

### Bot gets stuck or errors out
*   Check the terminal output for error messages.
*   If it gets stuck on a specific question, check the **Questions** tab in `config_ui.py` to ensure you have a valid answer configured for that type of question.

### AI Issues
*   If using OpenAI/DeepSeek/Gemini, ensure your API key is correctly set in the **Secrets** tab of the UI or in your `.env` file.
*   Make sure you have enough credits/quota for the API usage.

---

**Disclaimer**: This tool is for educational purposes. Use it responsibly and at your own risk. Be aware of LinkedIn's terms of service regarding automation.
