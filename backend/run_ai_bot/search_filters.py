"""Job search URL filters and pagination helpers."""

from run_ai_bot.bootstrap_env import *
from run_ai_bot.state import *

from modules.human_actions import human_move_and_click


def get_applied_job_ids() -> set[str]:
    """
    Function to get a `set` of applied job's Job IDs
    * Returns a set of Job IDs from existing applied jobs history csv file
    """
    job_ids: set[str] = set()
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                job_ids.add(row[0])
    except FileNotFoundError:
        print_lg(f"The CSV file '{file_name}' does not exist.")
    return job_ids


def set_search_location() -> None:
    """
    Function to set search location
    """
    if search_location.strip():
        try:
            print_lg(f'Setting search location as: "{search_location.strip()}"')
            search_location_ele = try_xp(
                driver,
                ".//input[@aria-label='City, state, or zip code'and not(@disabled)]",
                False,
            )  #  and not(@aria-hidden='true')]")
            text_input(driver, actions, search_location_ele, search_location, "Search Location")
        except ElementNotInteractableException:
            try_xp(
                driver,
                ".//label[@class='jobs-search-box__input-icon jobs-search-box__keywords-label']",
            )
            actions.send_keys(Keys.TAB, Keys.TAB).perform()
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            actions.send_keys(search_location.strip()).perform()
            sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            try_xp(driver, ".//button[@aria-label='Cancel']")
        except Exception as e:
            try_xp(driver, ".//button[@aria-label='Cancel']")
            print_lg(
                "Failed to update search location, continuing with default location!", e
            )


def apply_filters() -> None:
    """
    Function to apply job search filters
    """
    set_search_location()

    try:
        recommended_wait = 1 if click_gap < 1 else 0

        all_filters = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//button[normalize-space()="All filters"]')
            )
        )
        human_move_and_click(driver, all_filters)
        buffer(recommended_wait)

        wait_span_click(driver, sort_by)
        wait_span_click(driver, date_posted)
        buffer(recommended_wait)

        multi_sel_noWait(driver, experience_level)
        multi_sel_noWait(driver, companies, actions)
        if experience_level or companies:
            buffer(recommended_wait)

        multi_sel_noWait(driver, job_type)
        multi_sel_noWait(driver, on_site)
        if job_type or on_site:
            buffer(recommended_wait)

        if easy_apply_only:
            boolean_button_click(driver, actions, "Easy Apply")

        multi_sel_noWait(driver, location)
        multi_sel_noWait(driver, industry)
        if location or industry:
            buffer(recommended_wait)

        multi_sel_noWait(driver, job_function)
        multi_sel_noWait(driver, job_titles)
        if job_function or job_titles:
            buffer(recommended_wait)

        if under_10_applicants:
            boolean_button_click(driver, actions, "Under 10 applicants")
        if in_your_network:
            boolean_button_click(driver, actions, "In your network")
        if fair_chance_employer:
            boolean_button_click(driver, actions, "Fair Chance Employer")

        wait_span_click(driver, salary)
        buffer(recommended_wait)

        multi_sel_noWait(driver, benefits)
        multi_sel_noWait(driver, commitments)
        if benefits or commitments:
            buffer(recommended_wait)

        show_results_button: WebElement = driver.find_element(
            By.XPATH, '//button[contains(@aria-label, "Apply current filters to show")]'
        )
        human_move_and_click(driver, show_results_button)

        global pause_after_filters
        if pause_after_filters and "Turn off Pause after search" == pyautogui.confirm(
            "These are your configured search results and filter. It is safe to change them while this dialog is open, any changes later could result in errors and skipping this search run.",
            "Please check your results",
            ["Turn off Pause after search", "Look's good, Continue"],
        ):
            pause_after_filters = False

    except Exception as e:
        print_lg("Setting the preferences failed!")
        # print_lg(e)


def get_page_info() -> tuple[WebElement | None, int | None]:
    """
    Function to get pagination element and current page number
    """
    try:
        pagination_element = try_find_by_classes(
            driver,
            [
                "jobs-search-pagination__pages",
                "artdeco-pagination",
                "artdeco-pagination__pages",
            ],
        )
        scroll_to_view(driver, pagination_element)
        current_page = int(
            pagination_element.find_element(
                By.XPATH, "//button[contains(@class, 'active')]"
            ).text
        )
    except Exception as e:
        print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
        pagination_element = None
        current_page = None
        print_lg(e)
    return pagination_element, current_page
