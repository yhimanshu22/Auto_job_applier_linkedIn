"""CLI entry: validate config, login, AI clients, run loop, cleanup."""

import os
import sys

import pyautogui

from run_ai_bot.bootstrap_env import *
from run_ai_bot.login import is_logged_in_LN, login_LN
from run_ai_bot.pipeline import run
from run_ai_bot.session import load_cookies
from run_ai_bot.state import *


def main() -> None:
    try:
        global linkedIn_tab, tabs_count, useNewResume, aiClient
        alert_title = "Error Occurred. Closing Browser!"
        total_runs = 1
        validate_config()

        # Check for Resume existence
        if not os.path.exists(default_resume_path):
            pyautogui.alert(
                text=f'Your default resume "{default_resume_path}" is missing! Please update "default_resume_path" in config.py\n\nOR\n\nAdd a resume with exact name and path (check for spelling mistakes including cases).\n\n\nFor now the bot will continue using your previous upload from LinkedIn!',
                title="Missing Resume",
                button="OK",
            )
            useNewResume = False

        # --- Login Logic ---
        tabs_count = len(driver.window_handles)

        # 1. Open LinkedIn Homepage to set domain context for cookies
        driver.get("https://www.linkedin.com")

        # 2. Attempt to restore session from cookies
        load_cookies()

        # 3. Verify login status
        if not is_logged_in_LN():
            print_lg("Cookie login failed or first run. Logging in manually...")
            login_LN()
            # Note: login_LN() saves cookies internally upon success, so we don't need to call it again here.
        else:
            print_lg("Restored previous session successfully!")

        # 4. Final Safety Check before starting
        if not is_logged_in_LN():
            raise Exception(
                "Failed to login! Please check your credentials or internet connection."
            )

        linkedIn_tab = driver.current_window_handle

        # --- AI Client Setup ---
        if use_AI:
            if ai_provider == "openai":
                aiClient = ai_create_openai_client()
            ##> ------ Yang Li : MARKYangL - Feature ------
            elif ai_provider == "deepseek":
                aiClient = deepseek_create_client()
            elif ai_provider == "gemini":
                aiClient = gemini_create_client()
            elif ai_provider == "openclaw":
                aiClient = openclaw_create_client()
            ##<

            try:
                # Construct "About Me" string for AI context
                about_company_for_ai = " ".join(
                    [
                        word
                        for word in (first_name + " " + last_name).split()
                        if len(word) > 3
                    ]
                )
                print_lg(
                    f"Extracted about company info for AI: '{about_company_for_ai}'"
                )
            except Exception as e:
                print_lg("Failed to extract about company info!", e)

        # --- Job Application Loop ---
        driver.switch_to.window(linkedIn_tab)

        # Run the first cycle
        total_runs = run(total_runs)

        # Continue running if loop mode is enabled
        while run_non_stop:
            if cycle_date_posted:
                date_options = ["Any time", "Past month", "Past week", "Past 24 hours"]
                global date_posted
                # Cycle through date options logic
                date_posted = (
                    date_options[
                        (
                            date_options.index(date_posted) + 1
                            if date_options.index(date_posted) + 1 > len(date_options)
                            else -1
                        )
                    ]
                    if stop_date_cycle_at_24hr
                    else date_options[
                        (
                            0
                            if date_options.index(date_posted) + 1 >= len(date_options)
                            else date_options.index(date_posted) + 1
                        )
                    ]
                )

            if alternate_sortby:
                global sort_by
                sort_by = (
                    "Most recent" if sort_by == "Most relevant" else "Most relevant"
                )
                total_runs = run(total_runs)
                # Toggle back
                sort_by = (
                    "Most recent" if sort_by == "Most relevant" else "Most relevant"
                )

            total_runs = run(total_runs)

            if dailyEasyApplyLimitReached:
                print_lg("Daily limit reached. Stopping run loop.")
                break

    except (NoSuchWindowException, WebDriverException) as e:
        print_lg("Browser window closed or session is invalid. Exiting.", e)
    except Exception as e:
        critical_error_log("In Applier Main", e)
        pyautogui.alert(str(e), alert_title)
        sys.exit(1)
    finally:
        # --- Statistics & Cleanup ---
        print_lg("\n\nTotal runs:                     {}".format(total_runs))
        print_lg("Jobs Easy Applied:              {}".format(easy_applied_count))
        print_lg("External job links collected:   {}".format(external_jobs_count))
        print_lg("                              ----------")
        print_lg(
            "Total applied or collected:     {}".format(
                easy_applied_count + external_jobs_count
            )
        )
        print_lg("\nFailed jobs:                    {}".format(failed_count))
        print_lg("Irrelevant jobs skipped:        {}\n".format(skip_count))

        if randomly_answered_questions:
            print_lg(
                "\n\nQuestions randomly answered:\n  {}  \n\n".format(
                    ";\n".join(
                        str(question) for question in randomly_answered_questions
                    )
                )
            )

        quote = choice(
            [
                "You're one step closer than before.",
                "All the best with your future interviews.",
                "Keep up with the progress. You got this.",
                "If you're tired, learn to take rest but never give up.",
                "Success is not final, failure is not fatal: It is the courage to continue that counts. - Winston Churchill",
                "Believe in yourself and all that you are. Know that there is something inside you that is greater than any obstacle. - Christian D. Larson",
                "Every job is a self-portrait of the person who does it. Autograph your work with excellence.",
                "The only way to do great work is to love what you do. If you haven't found it yet, keep looking. Don't settle. - Steve Jobs",
                "Opportunities don't happen, you create them. - Chris Grosser",
                "The road to success and the road to failure are almost exactly the same. The difference is perseverance.",
                "Obstacles are those frightful things you see when you take your eyes off your goal. - Henry Ford",
                "The only limit to our realization of tomorrow will be our doubts of today. - Franklin D. Roosevelt",
            ]
        )
        msg = f"\n{quote}\n\n\nBest regards,\nHimanshu Yadav\nhttps://www.linkedin.com/in/yhimanshu22045/\n\n"
        pyautogui.alert(msg, "Exiting..")
        print_lg(msg, "Closing the browser...")

        if tabs_count >= 10:
            msg = "NOTE: IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM!\n\nOr it's highly likely that application will just open browser and not do anything next time!"
            pyautogui.alert(msg, "Info")
            print_lg("\n" + msg)

        ##> ------ Yang Li : MARKYangL - Feature ------
        if use_AI and aiClient:
            try:
                if ai_provider.lower() == "openai":
                    ai_close_openai_client(aiClient)
                elif ai_provider.lower() == "deepseek":
                    ai_close_openai_client(aiClient)
                elif ai_provider.lower() == "gemini":
                    pass  # Gemini client does not need to be closed
                elif ai_provider.lower() == "openclaw":
                    openclaw_close_client(aiClient)
                print_lg(f"Closed {ai_provider} AI client.")
            except Exception as e:
                print_lg("Failed to close AI client:", e)
        ##<

        try:
            if driver:
                driver.quit()
        except WebDriverException as e:
            print_lg("Browser already closed.", e)
        except Exception as e:
            critical_error_log("When quitting...", e)


if __name__ == "__main__":
    main()
