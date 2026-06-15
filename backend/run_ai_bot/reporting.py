"""CSV + DB logging for failures and successful submits."""

import os

from selenium.webdriver.remote.webdriver import WebDriver

from app_paths import get_logs_dir
from run_ai_bot.bootstrap_env import *
from run_ai_bot.session import log_to_db
from run_ai_bot.state import *

def failed_job(
    job_id: str,
    job_link: str,
    resume: str,
    date_listed,
    error: str,
    exception: Exception,
    application_link: str,
    screenshot_name: str,
) -> None:
    """
    Function to update failed jobs list in excel
    """
    try:
        with open(failed_file_name, "a", newline="", encoding="utf-8") as file:
            fieldnames = [
                "Job ID",
                "Job Link",
                "Resume Tried",
                "Date listed",
                "Date Tried",
                "Assumed Reason",
                "Stack Trace",
                "External Job link",
                "Screenshot Name",
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(
                {
                    "Job ID": truncate_for_csv(job_id),
                    "Job Link": truncate_for_csv(job_link),
                    "Resume Tried": truncate_for_csv(resume),
                    "Date listed": truncate_for_csv(date_listed),
                    "Date Tried": datetime.now(),
                    "Assumed Reason": truncate_for_csv(error),
                    "Stack Trace": truncate_for_csv(exception),
                    "External Job link": truncate_for_csv(application_link),
                    "Screenshot Name": truncate_for_csv(screenshot_name),
                }
            )
        
        # Log to DB
        log_to_db(
            status="failed",
            job_url=job_link,
            resume_used=resume,
            reason=f"{error}: {str(exception)}"
        )
        file.close()
    except Exception as e:
        print_lg("Failed to update failed jobs list!", e)
        pyautogui.alert(
            "Failed to update the excel of failed jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file",
            "Failed Logging",
        )


def screenshot(driver: WebDriver, job_id: str, failedAt: str) -> str:
    """
    Function to to take screenshot for debugging
    - Returns screenshot name as String
    """
    screenshot_name = "{} - {} - {}.png".format(job_id, failedAt, str(datetime.now()))
    path = os.path.join(
        get_logs_dir(), "screenshots", screenshot_name.replace(":", ".")
    )
    # special_chars = {'*', '"', '\\', '<', '>', ':', '|', '?'}
    # for char in special_chars:  path = path.replace(char, '-')
    driver.save_screenshot(path.replace("//", "/"))
    return screenshot_name


# >


def submitted_jobs(
    job_id: str,
    title: str,
    company: str,
    work_location: str,
    work_style: str,
    description: str,
    experience_required: int | Literal["Unknown", "Error in extraction"],
    skills: list[str] | Literal["In Development"],
    hr_name: str | Literal["Unknown"],
    hr_link: str | Literal["Unknown"],
    resume: str,
    reposted: bool,
    date_listed: datetime | Literal["Unknown"],
    date_applied: datetime | Literal["Pending"],
    job_link: str,
    application_link: str,
    questions_list: set | None,
    connect_request: Literal["In Development"],
) -> None:
    """
    Function to create or update the Applied jobs CSV file, once the application is submitted successfully
    """
    try:
        with open(file_name, mode="a", newline="", encoding="utf-8") as csv_file:
            fieldnames = [
                "Job ID",
                "Title",
                "Company",
                "Work Location",
                "Work Style",
                "About Job",
                "Experience required",
                "Skills required",
                "HR Name",
                "HR Link",
                "Resume",
                "Re-posted",
                "Date Posted",
                "Date Applied",
                "Job Link",
                "External Job link",
                "Questions Found",
                "Connect Request",
            ]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if csv_file.tell() == 0:
                writer.writeheader()
            writer.writerow(
                {
                    "Job ID": truncate_for_csv(job_id),
                    "Title": truncate_for_csv(title),
                    "Company": truncate_for_csv(company),
                    "Work Location": truncate_for_csv(work_location),
                    "Work Style": truncate_for_csv(work_style),
                    "About Job": truncate_for_csv(description),
                    "Experience required": truncate_for_csv(experience_required),
                    "Skills required": truncate_for_csv(skills),
                    "HR Name": truncate_for_csv(hr_name),
                    "HR Link": truncate_for_csv(hr_link),
                    "Resume": truncate_for_csv(resume),
                    "Re-posted": truncate_for_csv(reposted),
                    "Date Posted": truncate_for_csv(date_listed),
                    "Date Applied": truncate_for_csv(date_applied),
                    "Job Link": truncate_for_csv(job_link),
                    "External Job link": truncate_for_csv(application_link),
                    "Questions Found": truncate_for_csv(questions_list),
                    "Connect Request": truncate_for_csv(connect_request),
                }
            )
        
        # Log to DB
        log_to_db(
            status="applied",
            job_title=title,
            company=company,
            location=work_location,
            job_url=job_link,
            resume_used=resume,
            answer_generated=str(questions_list) if questions_list else None
        )
        csv_file.close()
    except Exception as e:
        print_lg("Failed to update submitted jobs list!", e)
        pyautogui.alert(
            "Failed to update the excel of applied jobs!\nProbably because of 1 of the following reasons:\n1. The file is currently open or in use by another program\n2. Permission denied to write to the file\n3. Failed to find the file",
            "Failed Logging",
        )


def is_easy_apply_modal_open() -> bool:
    try:
        for selector in (
            "[data-test-modal-id='easy-apply-modal']",
            ".jobs-easy-apply-modal",
        ):
            for modal in driver.find_elements(By.CSS_SELECTOR, selector):
                if modal.is_displayed():
                    return True
    except Exception:
        pass
    return False


# Function to discard the job application
def discard_job() -> None:
    try:
        actions.send_keys(Keys.ESCAPE).perform()
        buffer(0.5)
    except Exception:
        pass
    for label in ("Discard", "Discard application", "Dismiss"):
        try:
            if wait_span_click(driver, label, 1):
                return
        except Exception:
            pass
    try:
        from modules.clickers_and_finders import robust_click

        if robust_click(driver, ["Discard", "Dismiss", "Close"], 1):
            return
    except Exception:
        pass
    try:
        actions.send_keys(Keys.ESCAPE).perform()
    except Exception:
        pass

