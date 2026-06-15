from app_paths import get_logs_dir, get_runtime_writable_root
from modules.helpers import make_directories
from config.config_bridge import *

if stealth_mode:
    import undetected_chromedriver as uc
else:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    # from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from modules.helpers import (
    find_default_profile_directory,
    critical_error_log,
    print_lg,
    get_chrome_version,
)
import subprocess
import importlib.metadata
import hashlib
import os
import sys


def is_chrome_running():
    try:
        if os.name == "nt":
            output = subprocess.check_output("tasklist", shell=True).decode()
            return "chrome.exe" in output.lower()
        output = subprocess.check_output(
            ["pgrep", "-f", "chrome|chromium"], stderr=subprocess.DEVNULL
        ).decode()
        return bool(output.strip())
    except Exception:
        return False


def _clear_chrome_profile_locks(profile_dir: str) -> None:
    """Remove stale singleton locks left by crashed Chrome sessions."""
    for name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        path = os.path.join(profile_dir, name)
        if os.path.lexists(path):
            try:
                os.remove(path)
            except OSError:
                pass


def log_versions():
    try:
        uc_version = importlib.metadata.version("undetected-chromedriver")
        print_lg(f"Undetected Chromedriver Version: {uc_version}")
    except Exception:
        print_lg("Could not determine undetected-chromedriver version.")


try:
    _resume_dir = default_resume_path
except NameError:
    _resume_dir = "all resumes/default_resume.pdf"
try:
    _generated_resume_dir = generated_resume_path
except NameError:
    _generated_resume_dir = "all resumes/generated"

try:
    make_directories(
        [
            file_name,
            failed_file_name,
            os.path.join(get_logs_dir(), "screenshots"),
            _resume_dir,
            _generated_resume_dir + "/temp",
        ]
    )

    log_versions()

    # Detect Chrome version to avoid repeated downloads
    chrome_ver = get_chrome_version()
    if chrome_ver:
        print_lg(f"Detected Chrome Version: {chrome_ver}")
    else:
        print_lg("Could not detect Chrome version, will let UC decide.")

    # Check if Chrome is already running
    if is_chrome_running() and not safe_mode:
        print_lg(
            "WARNING: Chrome is already running! This might cause connection issues."
        )
        print_lg(
            "If you face 'session not created' error, please close all Chrome windows and try again."
        )

    # Set up WebDriver with Chrome Profile
    options = uc.ChromeOptions() if stealth_mode else Options()
    if run_in_background:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    if os.name != "nt":
        # Required on Linux servers: root-less sandbox and tiny /dev/shm
        # otherwise crash Chrome at startup or mid-session.
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
    if disable_extensions:
        options.add_argument("--disable-extensions")

    print_lg(
        "IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM! Or it's highly likely that application will just open browser and not do anything!"
    )

    if safe_mode:
        print_lg(
            "SAFE MODE: Will login with a guest profile, browsing history will not be saved in the browser!"
        )
    else:
        # User requested to remove persistent chrome_profile and use pickle for sessions instead
        # UC/Selenium will use a default temporary profile if no user-data-dir is provided
        print_lg("Using default/temporary browser profile (session persistence via cookies/pickle)")

    # One Chrome user-data-dir per supervisor bot so parallel runs do not share disk locks / state.
    _bot_tag = os.getenv("BOT_ID") or os.getenv("LINKEDIN_USERNAME", "default") or "default"
    _safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in str(_bot_tag))[:120]
    profile_dir = os.path.normpath(
        os.path.join(get_runtime_writable_root(), "chrome_profiles", _safe)
    )
    os.makedirs(profile_dir, exist_ok=True)
    _clear_chrome_profile_locks(profile_dir)
    options.add_argument(f"--user-data-dir={profile_dir}")
    _port = 9222 + (int(hashlib.md5(_safe.encode("utf-8")).hexdigest(), 16) % 800)
    options.add_argument(f"--remote-debugging-port={_port}")
    print_lg(f"Chrome profile dir (BOT_ID/account): {profile_dir}")
    print_lg(f"Chrome remote-debugging-port: {_port}")

    if stealth_mode:
        # try:
        #     driver = uc.Chrome(driver_executable_path="C:\\Program Files\\Google\\Chrome\\chromedriver-win64\\chromedriver.exe", options=options)
        # except (FileNotFoundError, PermissionError) as e:
        #     print_lg("(Undetected Mode) Got '{}' when using pre-installed ChromeDriver.".format(type(e).__name__))

        if chrome_ver:
            print_lg(f"Initializing UC with version_main={chrome_ver}...")
            driver = uc.Chrome(options=options, version_main=chrome_ver)
        else:
            print_lg(
                "Downloading Chrome Driver... This may take some time. Undetected mode requires download every run!"
            )
            driver = uc.Chrome(options=options)
    else:
        driver = webdriver.Chrome(
            options=options
        )  # , service=Service(executable_path="C:\\Program Files\\Google\\Chrome\\chromedriver-win64\\chromedriver.exe"))
    try:
        driver.maximize_window()
    except Exception:
        pass  # headless / no window manager
    wait = WebDriverWait(driver, 5)
    actions = ActionChains(driver)
except Exception as e:
    msg = 'Seems like either... \n\n1. Chrome is already running. \nA. Close all Chrome windows and try again. \n\n2. Google Chrome or Chromedriver is out dated. \nA. Update browser and Chromedriver (download a matching ChromeDriver for your Chrome version and ensure it is on PATH). \n\n3. If error occurred when using "stealth_mode", try reinstalling undetected-chromedriver. \nA. Open a terminal and use commands "pip uninstall undetected-chromedriver" and "pip install undetected-chromedriver". \n\n\nIf issue persists, try Safe Mode. Set, safe_mode = True in config.py \n\nPlease check GitHub discussions/support for solutions https://github.com/GodsScion/Auto_job_applier_linkedIn \n                                   OR \nReach out in discord ( https://discord.gg/fFp7uUzWCY )'
    if isinstance(e, TimeoutError):
        msg = "Couldn't download Chrome-driver. Set stealth_mode = False in config!"
    elif "session not created" in str(e).lower():
        msg = "CRITICAL: Session not created! Chrome is likely already running with a profile lock.\nPLEASE CLOSE ALL CHROME WINDOWS and try again."

    print_lg(msg)
    critical_error_log("In Opening Chrome", e)
    from modules.gui_safe import alert

    alert(msg, "Error in opening chrome")
    try:
        driver.quit()
    except NameError:
        sys.exit(1)
