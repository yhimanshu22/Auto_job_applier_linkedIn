"""External apply tab flow and company follow checkbox."""

from selenium.webdriver.remote.webdriver import WebDriver

from run_ai_bot.bootstrap_env import *
from run_ai_bot.humanize import human_click
from run_ai_bot.reporting import failed_job
from run_ai_bot.state import *


def external_apply(
    pagination_element: WebElement,
    job_id: str,
    job_link: str,
    resume: str,
    date_listed,
    application_link: str,
    screenshot_name: str,
) -> tuple[bool, str, int]:
    """
    Function to open new tab and save external job application links
    """
    global tabs_count, dailyEasyApplyLimitReached
    if easy_apply_only:
        limit_reached_msg = False
        try:
            feedback = driver.find_element(By.CLASS_NAME, "artdeco-inline-feedback__message").text
            if "exceeded the daily application limit" in feedback.lower():
                dailyEasyApplyLimitReached = True
                limit_reached_msg = True
                print_lg("LinkedIn daily Easy Apply limit reached.")
        except:
            pass
        
        if not limit_reached_msg:
            print_lg("Job is not an Easy Apply job. Skipping as per easy_apply_only=True.")

        return True, application_link, tabs_count
    try:
        apply_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3')]",
                )
            )
        )  # './/button[contains(span, "Apply") and not(span[contains(@class, "disabled")])]'
        human_click(apply_btn)
        wait_span_click(driver, "Continue", 1, True, False)
        windows = driver.window_handles
        tabs_count = len(windows)
        driver.switch_to.window(windows[-1])
        application_link = driver.current_url
        print_lg('Got the external application link "{}"'.format(application_link))
        if close_tabs and driver.current_window_handle != linkedIn_tab:
            driver.close()
        driver.switch_to.window(linkedIn_tab)
        return False, application_link, tabs_count
    except Exception as e:
        # print_lg(e)
        print_lg("Failed to apply!")
        failed_job(
            job_id,
            job_link,
            resume,
            date_listed,
            "Probably didn't find Apply button or unable to switch tabs.",
            e,
            application_link,
            screenshot_name,
        )
        global failed_count
        failed_count += 1
        return True, application_link, tabs_count


def follow_company(modal: WebDriver = driver) -> None:
    """
    Function to follow or un-follow easy applied companies based om `follow_companies`
    """
    try:
        follow_checkbox_input = try_xp(
            modal, ".//input[@id='follow-company-checkbox' and @type='checkbox']", False
        )
        if (
            follow_checkbox_input
            and follow_checkbox_input.is_selected() != follow_companies
        ):
            try_xp(modal, ".//label[@for='follow-company-checkbox']")
    except Exception as e:
        print_lg("Failed to update follow companies checkbox!", e)
