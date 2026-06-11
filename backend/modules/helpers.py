# Imports

import os
import sys
import json
import pathlib

from time import sleep
from random import randint
from datetime import datetime, timedelta
from modules.gui_safe import alert
from pprint import pprint

from app_paths import get_logs_dir
from config.config_bridge import *
from utils.logger import logger as cloud_logger


#### Common functions ####


# < Directories related
def make_directories(paths: list[str]) -> None:
    """
    Function to create missing directories
    """
    for path in paths:
        path = os.path.expanduser(path)  # Expands ~ to user's home directory
        path = path.replace("//", "/")

        # If path looks like a file path, get the directory part
        if "." in os.path.basename(path):
            path = os.path.dirname(path)

        if not path:  # Handle cases where path is empty after dirname
            continue

        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)  # exist_ok=True avoids race condition
        except Exception as e:
            print(f'Error while creating directory "{path}": ', e)


def find_default_profile_directory() -> str | None:
    """
    Dynamically finds the default Google Chrome 'User Data' directory path
    across Windows, macOS, and Linux, regardless of OS version.

    Returns the absolute path as a string, or None if the path is not found.
    """

    home = pathlib.Path.home()

    # Windows
    if sys.platform.startswith("win"):
        paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Local\Google\Chrome\User Data"),
            os.path.expandvars(
                r"%USERPROFILE%\Local Settings\Application Data\Google\Chrome\User Data"
            ),
        ]
    # Linux
    elif sys.platform.startswith("linux"):
        paths = [
            str(home / ".config" / "google-chrome"),
            str(
                home
                / ".var"
                / "app"
                / "com.google.Chrome"
                / "data"
                / ".config"
                / "google-chrome"
            ),
        ]
    # MacOS ## For some reason, opening with profile in MacOS is not creating a session for undetected-chromedriver!
    # elif sys.platform == 'darwin':
    #     paths = [
    #         str(home / "Library" / "Application Support" / "Google" / "Chrome")
    #     ]
    else:
        return None

    # Check each potential path and return the first one that exists
    for path_str in paths:
        if os.path.exists(path_str):
            return path_str

    return None


# >


# < Logging related
def critical_error_log(possible_reason: str, stack_trace: Exception) -> None:
    """
    Function to log and print critical errors along with datetime stamp
    """
    print_lg(possible_reason, stack_trace, datetime.now(), from_critical=True)


def get_log_path():
    """
    Log files live under get_logs_dir() (backend/logs in dev), not cwd.
    When BOT_ID is set (supervisor-spawned worker), logs go to bot-<id>.txt per profile.
    """
    try:
        base = get_logs_dir()
        bid = os.getenv("BOT_ID", "").strip()
        if bid:
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in bid)
            return os.path.join(base, f"bot-{safe}.txt")
        return os.path.join(base, "log.txt")
    except Exception as e:
        critical_error_log(
            "Failed getting log path! So assigning fallback under app logs dir.",
            e,
        )
        return os.path.join(get_logs_dir(), "log.txt")


__logs_file_path = get_log_path()


def print_lg(
    *msgs: str | dict,
    end: str = "\n",
    pretty: bool = False,
    flush: bool = False,
    from_critical: bool = False,
) -> None:
    """
    Function to log and print. 
    Now integrates with Google Cloud Logging.
    """
    try:
        combined_msg = " ".join([str(m) for m in msgs])
        
        # Log to Cloud/Console via our new logger
        if from_critical:
            cloud_logger.error(combined_msg)
        else:
            cloud_logger.info(combined_msg)

        # Still keep local file logging for redundancy/dev
        with open(__logs_file_path, "a+", encoding="utf-8") as file:
            file.write(combined_msg + end)
            
    except Exception as e:
        print(f"Logging error: {e}")


# >


def buffer(speed: int = 0) -> None:
    """
    Function to wait within a period of selected random range.
    * Will not wait if input `speed <= 0`
    * Multiplier applied based on 'bot_speed' setting (1-10, default 5)
    """
    if speed <= 0:
        return
    
    # Load bot_speed from config or default to 5
    # Speed 10 = fastest (0.2x delay), Speed 1 = slowest (2.0x delay)
    from config.config_bridge import bot_speed
    try:
        speed_val = int(bot_speed)
    except:
        speed_val = 5
        
    user_id = os.getenv("USER_ID", "local-user")
    is_admin = user_id == "local-user" or os.getenv("USER_EMAIL") == "himu09854@gmail.com"
    if is_admin:
        speed_val = max(speed_val, 9)

    multiplier = max(0.05, (11 - speed_val) / 5.0) # Speed 10 -> 0.2, Speed 5 -> 1.2, Speed 1 -> 2.0
    
    # Apply multiplier to the base logic
    if speed <= 1 and speed < 2:
        wait_time = randint(6, 10) * 0.1 * multiplier
    elif speed <= 2 and speed < 3:
        wait_time = randint(10, 18) * 0.1 * multiplier
    else:
        wait_time = randint(18, round(speed) * 10) * 0.1 * multiplier
        
    return sleep(wait_time)


def random_sleep(min_time=1.0, max_time=None):
    """Sleeps for a random amount of time to simulate human processing."""
    user_id = os.getenv("USER_ID", "local-user")
    is_admin = user_id == "local-user" or os.getenv("USER_EMAIL") == "himu09854@gmail.com"
    
    if max_time is None:
        max_time = min_time + 2.0  # Add 2 seconds jitter by default

    # Load speed from config
    from config.config_bridge import bot_speed
    try:
        speed_val = int(bot_speed)
    except:
        speed_val = 5

    # Privileged users get a speed boost
    if is_admin:
        speed_val = max(speed_val, 9)

    multiplier = max(0.05, (11 - speed_val) / 5.0)

    # Ensure times are valid
    if min_time < 0.1:
        min_time = 0.1
    if max_time <= min_time:
        max_time = min_time + 0.5

    duration = (randint(int(min_time * 100), int(max_time * 100)) / 100.0) * multiplier
    
    if duration > 0:
        sleep(duration)


def manual_login_retry(is_logged_in: callable, limit: int = 2) -> None:
    """
    Function to ask and validate manual login
    """
    count = 0
    while not is_logged_in():
        from modules.gui_safe import alert

        print_lg("Seems like you're not logged in!")
        button = "Confirm Login"
        message = (
            'After you successfully Log In, please click "{}" button below.'.format(
                button
            )
        )
        if count > limit:
            button = "Skip Confirmation"
            message = 'If you\'re seeing this message even after you logged in, Click "{}". Seems like auto login confirmation failed!'.format(
                button
            )
        count += 1
        if alert(message, "Login Required", button) and count > limit:
            return


def calculate_date_posted(time_string: str) -> datetime | None | ValueError:
    """
    Function to calculate date posted from string.
    Returns datetime object | None if unable to calculate | ValueError if time_string is invalid
    Valid time string examples:
    * 10 seconds ago
    * 15 minutes ago
    * 2 hours ago
    * 1 hour ago
    * 1 day ago
    * 10 days ago
    * 1 week ago
    * 1 month ago
    * 1 year ago
    """
    import re

    time_string = time_string.strip()
    now = datetime.now()

    match = re.search(
        r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago",
        time_string,
        re.IGNORECASE,
    )

    if match:
        try:
            value = int(match.group(1))
            unit = match.group(2).lower()

            if "second" in unit:
                return now - timedelta(seconds=value)
            elif "minute" in unit:
                return now - timedelta(minutes=value)
            elif "hour" in unit:
                return now - timedelta(hours=value)
            elif "day" in unit:
                return now - timedelta(days=value)
            elif "week" in unit:
                return now - timedelta(weeks=value)
            elif "month" in unit:
                return now - timedelta(days=value * 30)  # Approximation
            elif "year" in unit:
                return now - timedelta(days=value * 365)  # Approximation
        except (ValueError, IndexError):
            # Fallback for cases where parsing fails
            pass

    # If regex doesn't match, or parsing failed, return None.
    # This will skip jobs where the date can't be determined, preventing crashes.
    return None


def convert_to_lakhs(value: str) -> str:
    """
    Converts str value to lakhs, no validations are done except for length and stripping.
    Examples:
    * "100000" -> "1.00"
    * "101,000" -> "10.1," Notice ',' is not removed
    * "50" -> "0.00"
    * "5000" -> "0.05"
    """
    value = value.strip()
    l = len(value)
    if l > 0:
        if l > 5:
            value = value[: l - 5] + "." + value[l - 5 : l - 3]
        else:
            value = "0." + "0" * (5 - l) + value[:2]
    return value


def convert_to_json(data) -> dict:
    """
    Function to convert data to JSON, if unsuccessful, returns `{"error": "Unable to parse the response as JSON", "data": data}`
    """
    try:
        result_json = json.loads(data)
        return result_json
    except json.JSONDecodeError:
        return {"error": "Unable to parse the response as JSON", "data": data}


def truncate_for_csv(
    data, max_length: int = 131000, suffix: str = "...[TRUNCATED]"
) -> str:
    """
    Function to truncate data for CSV writing to avoid field size limit errors.
    * Takes in `data` of any type and converts to string
    * Takes in `max_length` of type `int` - maximum allowed length (default: 131000, leaving room for suffix)
    * Takes in `suffix` of type `str` - text to append when truncated
    * Returns truncated string if data exceeds max_length
    """
    try:
        # Convert data to string
        str_data = str(data) if data is not None else ""

        # If within limit, return as-is
        if len(str_data) <= max_length:
            return str_data

        # Truncate and add suffix
        truncated = str_data[: max_length - len(suffix)] + suffix
        return truncated
    except Exception as e:
        return f"[ERROR CONVERTING DATA: {e}]"


def get_chrome_version() -> int | None:
    """
    Detects the installed Google Chrome version on Windows.
    Returns the major version number (e.g., 131) or None if not found.
    """
    if sys.platform.startswith("win"):
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"
            )
            version, _ = winreg.QueryValueEx(key, "version")
            return int(version.split(".")[0])
        except Exception:
            try:
                # Fallback to HKEY_LOCAL_MACHINE
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\WOW6432Node\Google\Update\Clients\{8A69D345-D564-463c-AFF1-A69D9E530F96}",
                )
                version, _ = winreg.QueryValueEx(key, "pv")
                return int(version.split(".")[0])
            except Exception:
                pass
    return None


def check_deal_breakers(description_text: str) -> tuple[bool, str]:
    """
    Scans the job description for deal-breaker phrases using Regex.
    Returns: (bool, str) -> (Should_Skip, Reason)
    """
    import re
    from config.config_bridge import (
        visa_deal_breakers,
        location_blacklists,
        tech_blacklists,
        education_blacklists,
    )

    try:
        from config.config_bridge import require_visa
    except ImportError:
        require_visa = False

    text_lower = description_text.lower()

    # 1. Check Visa/Citizenship (Only if you need a visa)
    if require_visa:
        # We only care about "US Citizen" requirements if we actually need a visa.
        # If require_visa is True, it means we DO need sponsorship, so we must skip "Citizenship Only" jobs.
        for phrase in visa_deal_breakers:
            # Check if it's a raw string regex or just text
            if phrase.startswith(r"\\") or "\\" in phrase or "[" in phrase:
                pattern = phrase  # It's already a regex
            else:
                # \b ensures we match whole words (e.g., avoids matching "reuse" when looking for "us")
                pattern = r"\b" + re.escape(phrase) + r"\b"

            if re.search(pattern, text_lower, re.IGNORECASE):
                return True, f"Visa Deal Breaker: Found '{phrase}'"

    # 2. Check Tech Stack Blacklist
    for phrase in tech_blacklists:
        pattern = r"\b" + re.escape(phrase) + r"\b"
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True, f"Tech Stack Deal Breaker: Found '{phrase}'"

    # 3. Check Location Strictness
    for phrase in location_blacklists:
        if phrase in text_lower:
            return True, f"Location Deal Breaker: Found '{phrase}'"

    # 4. Check Education Strictness
    for phrase in education_blacklists:
        if phrase in text_lower:
            return True, f"Education Deal Breaker: Found '{phrase}'"

    return False, "Safe"
