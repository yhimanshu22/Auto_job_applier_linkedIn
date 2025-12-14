from modules.helpers import make_directories
from config.settings import (
    run_in_background,
    stealth_mode,
    disable_extensions,
    safe_mode,
    file_name,
    failed_file_name,
    logs_folder_path,
    generated_resume_path,
)
from config.questions import default_resume_path

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
import pkg_resources
import os


def is_chrome_running():
    try:
        # Check if chrome.exe is running using tasklist
        output = subprocess.check_output("tasklist", shell=True).decode()
        return "chrome.exe" in output.lower()
    except Exception:
        return False


def log_versions():
    try:
        uc_version = pkg_resources.get_distribution("undetected-chromedriver").version
        print_lg(f"Undetected Chromedriver Version: {uc_version}")
    except Exception:
        print_lg("Could not determine undetected-chromedriver version.")


try:
    make_directories(
        [
            file_name,
            failed_file_name,
            logs_folder_path + "/screenshots",
            default_resume_path,
            generated_resume_path + "/temp",
            "chrome_profile",  # Ensure local profile dir exists
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
        options.add_argument("--headless")
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
        # Use LOCAL profile directory to avoid conflicts and ensure persistence
        profile_dir = os.path.join(os.getcwd(), "chrome_profile")
        options.add_argument(f"--user-data-dir={profile_dir}")
        print_lg(f"Using local profile: {profile_dir}")

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
    driver.maximize_window()
    wait = WebDriverWait(driver, 5)
    actions = ActionChains(driver)
except Exception as e:
    msg = 'Seems like either... \n\n1. Chrome is already running. \nA. Close all Chrome windows and try again. \n\n2. Google Chrome or Chromedriver is out dated. \nA. Update browser and Chromedriver (You can run "windows-setup.bat" in /setup folder for Windows PC to update Chromedriver)! \n\n3. If error occurred when using "stealth_mode", try reinstalling undetected-chromedriver. \nA. Open a terminal and use commands "pip uninstall undetected-chromedriver" and "pip install undetected-chromedriver". \n\n\nIf issue persists, try Safe Mode. Set, safe_mode = True in config.py \n\nPlease check GitHub discussions/support for solutions https://github.com/GodsScion/Auto_job_applier_linkedIn \n                                   OR \nReach out in discord ( https://discord.gg/fFp7uUzWCY )'
    if isinstance(e, TimeoutError):
        msg = "Couldn't download Chrome-driver. Set stealth_mode = False in config!"
    elif "session not created" in str(e).lower():
        msg = "CRITICAL: Session not created! Chrome is likely already running with a profile lock.\nPLEASE CLOSE ALL CHROME WINDOWS and try again."

    print_lg(msg)
    critical_error_log("In Opening Chrome", e)
    from pyautogui import alert

    alert(msg, "Error in opening chrome")
    try:
        driver.quit()
    except NameError:
        exit()
