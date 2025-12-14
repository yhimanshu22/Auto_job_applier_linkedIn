# LinkedIn AI Auto Job Applier

Welcome! This bot automates the process of applying to jobs on LinkedIn. It searches for relevant jobs, answers application questions, and submits applications for you—saving you hours of manual work.

---

## Quick Start Guide

Follow these steps to get the bot running in minutes!

### 1. Prerequisites
*   **Python 3.10+**: [Download Here](https://www.python.org/downloads/) (Make sure to check "Add Python to PATH" during installation).
*   **Google Chrome**: [Download Here](https://www.google.com/chrome).

### 2. Installation
1.  **Clone or Download** this repository.
2.  Open a terminal (Command Prompt or PowerShell) in the project folder.
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(If `requirements.txt` is missing, run: `pip install undetected-chromedriver pyautogui setuptools openai flask-cors flask`)*

4.  **Setup Drivers**:
    *   **Windows**: Double-click `setup/windows-setup.bat` to automatically download the correct ChromeDriver.

### 3. Configuration (The Important Part!)
You need to tell the bot who you are and what jobs you want. Edit the files in the `config/` folder:

*   **`config/personals.py`**: Enter your personal details (Name, Address, Phone, etc.).
*   **`config/questions.py`**: Answer common application questions (Experience, Visa sponsorship, etc.).
    *   *Tip*: Set `us_citizenship = "Decline"` or `"Other"` if you don't want to specify.
*   **`config/secrets.py`**:
    *   `username`: Your LinkedIn email.
    *   `password`: Your LinkedIn password.
    *   `llm_api_key`: (Optional) OpenAI or DeepSeek API key for AI-generated answers.
*   **`config/search.py`**: Define your job search:
    *   `search_terms`: List of job titles (e.g., `["Software Engineer", "Python Developer"]`).
    *   `search_location`: Where to look (e.g., `"United States"`, `"Remote"`).
*   **`config/settings.py`**:
    *   `stealth_mode = True`: Recommended to avoid detection.
    *   `safe_mode = False`: Set to `True` if you have trouble connecting to Chrome (uses a Guest profile).

### 4. Run the Bot
1.  **Close all existing Google Chrome windows.**
2.  Run the command:
    ```bash
    python runAiBot.py
    ```
3.  Sit back and watch it apply! 

---

## 🛠️ Configuration Details

Here is a quick reference for what each config file does:

| File | Purpose | Key Settings |
| :--- | :--- | :--- |
| **`personals.py`** | Your Identity | Name, Address, Contact Info, Ethnicity, Gender. |
| **`questions.py`** | Application Answers | Years of Experience, Visa Status, Salary Expectations, Links (Portfolio, LinkedIn). |
| **`secrets.py`** | Credentials | LinkedIn Login, AI API Keys. |
| **`search.py`** | Job Filters | Job Titles, Location, Experience Level, Job Type (Full-time/Contract), Blacklisted Companies. |
| **`settings.py`** | Bot Behavior | `stealth_mode`, `safe_mode`, `run_in_background`, `disable_extensions`. |

---

## ❓ Troubleshooting

### "Session not created" or "Chrome not connecting"
*   **Cause**: Chrome is likely already running or there is a version mismatch.
*   **Fix**: 
    1.  **Close ALL Chrome windows** and try again.
    2.  If that fails, set `safe_mode = True` in `config/settings.py`.
    3.  Check if your Chrome browser updated recently. You might need to re-run `setup/windows-setup.bat`.

### Bot gets stuck or errors out
*   Check the terminal output for error messages.
*   If it gets stuck on a specific question, check `config/questions.py` to ensure you have a valid answer configured.

**Disclaimer**: This tool is for educational purposes. Use it responsibly and at your own risk. Be aware of LinkedIn's terms of service regarding automation.
