"""Main job search loop: listings, Easy Apply, external apply."""

import os

from run_ai_bot.bootstrap_env import *
from run_ai_bot.easy_apply import answer_questions, upload_resume
from run_ai_bot.external_apply import external_apply, follow_company
from run_ai_bot.humanize import human_click
from run_ai_bot.job_details import (
    check_blacklist,
    get_job_description,
    get_job_main_details,
)
from run_ai_bot.reporting import discard_job, failed_job, screenshot, submitted_jobs
from run_ai_bot.search_filters import get_applied_job_ids, get_page_info
from run_ai_bot.state import *

from modules.human_actions import human_move_and_click


def run(total_runs: int) -> int:
    if dailyEasyApplyLimitReached:
        return total_runs
    print_lg(
        "\n########################################################################################################################\n"
    )
    print_lg(f"Date and Time: {datetime.now()}")
    print_lg(f"Cycle number: {total_runs}")
    print_lg(
        f"Currently looking for jobs posted within '{date_posted}' and sorting them by '{sort_by}'"
    )
    apply_to_jobs(search_terms)
    print_lg(
        "########################################################################################################################\n"
    )
    if not dailyEasyApplyLimitReached:
        if is_admin_user:
            print_lg("Admin user detected. Skipping 10 min sleep.")
        else:
            print_lg("Sleeping for 10 min...")
            sleep(300)
            print_lg("Few more min... Gonna start with in next 5 min...")
            sleep(300)
    random_sleep(2, 4)
    return total_runs + 1


def apply_to_jobs(search_terms: list[str]) -> None:
    applied_jobs = get_applied_job_ids()
    rejected_jobs = set()
    blacklisted_companies = set()
    global current_city, failed_count, skip_count, easy_applied_count, external_jobs_count, tabs_count, pause_before_submit, pause_at_failed_question, useNewResume, dailyEasyApplyLimitReached
    current_city = current_city.strip()

    if randomize_search_order:
        shuffle(search_terms)

    for searchTerm in search_terms:
        # Construct URL with parameters to avoid unreliable UI clicks
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = [f"keywords={searchTerm}"]

        # 1. Location Logic
        if search_location:
            if search_location.lower().strip() == "india":
                params.append("geoId=102713980")
            else:
                params.append(f"location={search_location}")

        # 2. Date Posted Logic (f_TPR)
        date_mapping = {
            "Past 24 hours": "r86400",
            "Past week": "r604800",
            "Past month": "r2592000",
        }
        if date_posted in date_mapping:
            params.append(f"f_TPR={date_mapping[date_posted]}")

        # 3. Experience Level Logic (f_E)
        exp_mapping = {
            "Internship": "1",
            "Entry level": "2",
            "Associate": "3",
            "Mid-Senior level": "4",
            "Director": "5",
            "Executive": "6",
        }
        if experience_level:
            exp_values = [exp_mapping[e] for e in experience_level if e in exp_mapping]
            if exp_values:
                params.append(f"f_E={','.join(exp_values)}")

        # 4. Job Type Logic (f_JT)
        jt_mapping = {
            "Full-time": "F",
            "Part-time": "P",
            "Contract": "C",
            "Temporary": "T",
            "Volunteer": "V",
            "Internship": "I",
        }
        if job_type:
            jt_values = [jt_mapping[j] for j in job_type if j in jt_mapping]
            if jt_values:
                params.append(f"f_JT={','.join(jt_values)}")

        # 5. Remote/On-site Logic (f_WT)
        wt_mapping = {"On-site": "1", "Remote": "2", "Hybrid": "3"}
        if on_site:
            wt_values = [wt_mapping[w] for w in on_site if w in wt_mapping]
            if wt_values:
                params.append(f"f_WT={','.join(wt_values)}")

        # 6. Easy Apply Logic (f_AL)
        if easy_apply_only:
            params.append("f_AL=true")

        # Construct final URL
        full_url = base_url + "&".join(params)

        driver.get(full_url)
        print_lg(
            "\n________________________________________________________________________________________________________________________\n"
        )
        print_lg(f'\n>>>> Now searching for "{searchTerm}" <<<<\n')
        print_lg(f"URL: {full_url}\n\n")

        current_count = 0
        try:
            while current_count < switch_number:
                # Wait until job listings are loaded
                wait.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//li[@data-occludable-job-id]")
                    )
                )

                pagination_element, current_page = get_page_info()

                # Find all job listings in current page
                random_sleep(2, 4)
                job_listings = driver.find_elements(
                    By.XPATH, "//li[@data-occludable-job-id]"
                )

                for job in job_listings:
                    if keep_screen_awake:
                        pyautogui.press("shiftright")
                    if current_count >= switch_number:
                        break

                    print_lg("\n-@-\n")

                    job_id, title, company, work_location, work_style, skip = (
                        get_job_main_details(job, blacklisted_companies, rejected_jobs)
                    )

                    if skip:
                        continue

                    # Redundant fail safe check for applied jobs!
                    try:
                        if job_id in applied_jobs or find_by_class(
                            driver, "jobs-s-apply__application-link", 2
                        ):
                            print_lg(
                                f'Already applied to "{title} | {company}" job. Job ID: {job_id}!'
                            )
                            continue
                    except Exception as e:
                        print_lg(
                            f'Trying to Apply to "{title} | {company}" job. Job ID: {job_id}'
                        )

                    job_link = "https://www.linkedin.com/jobs/view/" + job_id
                    application_link = "Easy Applied"
                    date_applied = "Pending"
                    hr_link, hr_name, date_listed = "Unknown", "Unknown", "Unknown"
                    skills, resume, reposted = "Not extracted", "Pending", False
                    questions_list, screenshot_name = None, "Not Available"

                    try:
                        rejected_jobs, blacklisted_companies, jobs_top_card = (
                            check_blacklist(
                                rejected_jobs, job_id, company, blacklisted_companies
                            )
                        )
                    except ValueError as e:
                        print_lg(e, "Skipping this job!\n")
                        failed_job(
                            job_id,
                            job_link,
                            resume,
                            date_listed,
                            "Found Blacklisted words in About Company",
                            e,
                            "Skipped",
                            screenshot_name,
                        )
                        skip_count += 1
                        continue
                    except Exception as e:
                        print_lg("Failed to scroll to About Company!")

                    # Hiring Manager info
                    try:
                        hr_info_card = WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located(
                                (By.CLASS_NAME, "hirer-card__hirer-information")
                            )
                        )
                        hr_link = hr_info_card.find_element(
                            By.TAG_NAME, "a"
                        ).get_attribute("href")
                        hr_name = hr_info_card.find_element(By.TAG_NAME, "span").text
                    except Exception as e:
                        print_lg(
                            f'HR info was not given for "{title}" with Job ID: {job_id}!'
                        )

                    # Calculation of date posted
                    try:
                        time_posted_text = jobs_top_card.find_element(
                            By.XPATH, './/span[contains(normalize-space(), " ago")]'
                        ).text
                        print("Time Posted: " + time_posted_text)
                        if time_posted_text.__contains__("Reposted"):
                            reposted = True
                            time_posted_text = time_posted_text.replace("Reposted", "")
                        date_listed = calculate_date_posted(time_posted_text.strip())
                    except Exception as e:
                        print_lg("Failed to calculate the date posted!", e)

                    description, experience_required, skip, reason, message = (
                        get_job_description()
                    )

                    # --- NON-AI DEAL BREAKER CHECK ---
                    if not skip:
                        is_deal_breaker, breaker_reason = check_deal_breakers(
                            description
                        )
                        if is_deal_breaker:
                            skip = True
                            reason = "Deal Breaker Rule"
                            message = f"{breaker_reason}. Skipping this job!"

                    if skip:
                        print_lg(message)
                        failed_job(
                            job_id,
                            job_link,
                            resume,
                            date_listed,
                            reason,
                            message,
                            "Skipped",
                            screenshot_name,
                        )
                        rejected_jobs.add(job_id)
                        skip_count += 1
                        continue

                    # AI is used only for Easy Apply question answers (see answer_questions), not job/skill parsing.

                    uploaded = False
                    # Case 1: Easy Apply Button
                    xpath_easy_apply = ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3') and contains(@aria-label, 'Easy')]"
                    is_easy_apply = False
                    try:
                        # Wait for the button to be present and clickable
                        easy_apply_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, xpath_easy_apply))
                        )
                        scroll_to_view(driver, easy_apply_button)
                        human_move_and_click(driver, easy_apply_button)
                        is_easy_apply = True
                    except:
                        is_easy_apply = False

                    if is_easy_apply:
                        try:
                            errored = ""
                            modal = find_by_class(driver, "jobs-easy-apply-modal")
                            wait_span_click(modal, "Next", 1) or robust_click(
                                driver, ["Next"], 1
                            )

                            resume = "Previous resume"
                            next_button = True
                            questions_list = set()
                            next_counter = 0

                            while next_button:
                                next_counter += 1
                                if next_counter >= 15:
                                    if pause_at_failed_question:
                                        screenshot(
                                            driver, job_id, "Needed manual intervention"
                                        )
                                        pyautogui.alert(
                                            "Help needed at questions. Click Continue when done.",
                                            "Help Needed",
                                            "Continue",
                                        )
                                        next_counter = 1
                                        continue

                                    screenshot_name = screenshot(
                                        driver, job_id, "Failed at questions"
                                    )
                                    errored = "stuck"
                                    raise Exception("Stuck in Next loop")

                                questions_list = answer_questions(
                                    modal,
                                    questions_list,
                                    work_location,
                                    job_description=description,
                                )

                                if useNewResume and not uploaded:
                                    uploaded, resume = upload_resume(
                                        modal, default_resume_path
                                    )

                                try:
                                    next_button = modal.find_element(
                                        By.XPATH, './/span[normalize-space(.)="Review"]'
                                    )
                                except NoSuchElementException:
                                    try:
                                        next_button = modal.find_element(
                                            By.XPATH,
                                            './/button[contains(span, "Next")]',
                                        )
                                    except NoSuchElementException:
                                        break  # Final screen

                                human_move_and_click(driver, next_button)
                                buffer(click_gap)

                            wait_span_click(
                                driver, "Review", 1, scrollTop=True
                            ) or robust_click(driver, ["Review"], 1)

                            if errored != "stuck" and pause_before_submit:
                                decision = pyautogui.confirm(
                                    "Review info. Do not click Submit manually.",
                                    "Confirm",
                                    [
                                        "Disable Pause",
                                        "Discard Application",
                                        "Submit Application",
                                    ],
                                )
                                if decision == "Discard Application":
                                    raise Exception("User discarded job")
                                if decision == "Disable Pause":
                                    pause_before_submit = False

                            follow_company(modal)

                            if wait_span_click(
                                driver, "Submit application", 2, scrollTop=True
                            ) or robust_click(driver, ["Submit application"], 2):
                                date_applied = datetime.now()
                                if not (
                                    wait_span_click(driver, "Done", 2)
                                    or robust_click(driver, ["Done"], 2)
                                ):
                                    actions.send_keys(Keys.ESCAPE).perform()
                            else:
                                raise Exception("Failed to click Submit")

                        except Exception as e:
                            print_lg("Failed to Easy apply!", e)
                            failed_job(
                                job_id,
                                job_link,
                                resume,
                                date_listed,
                                "Problem in Easy Applying",
                                e,
                                application_link,
                                screenshot_name,
                            )
                            failed_count += 1
                            discard_job()
                            continue
                    else:
                        # Case 2: Apply externally
                        skip, application_link, tabs_count = external_apply(
                            pagination_element,
                            job_id,
                            job_link,
                            resume,
                            date_listed,
                            application_link,
                            screenshot_name,
                        )
                        if dailyEasyApplyLimitReached:
                            return
                        if skip:
                            continue

                    submitted_jobs(
                        job_id,
                        title,
                        company,
                        work_location,
                        work_style,
                        description,
                        experience_required,
                        skills,
                        hr_name,
                        hr_link,
                        resume,
                        reposted,
                        date_listed,
                        date_applied,
                        job_link,
                        application_link,
                        questions_list,
                        "In Development",
                    )

                    if uploaded:
                        useNewResume = False
                    current_count += 1
                    if application_link == "Easy Applied":
                        easy_applied_count += 1
                        if not is_admin_user and easy_applied_count >= daily_apply_limit:
                            print_lg(f"Daily Easy Apply limit reached: {daily_apply_limit}")
                            dailyEasyApplyLimitReached = True
                            return
                    else:
                        external_jobs_count += 1
                    applied_jobs.add(job_id)

                if pagination_element == None:
                    break
                try:
                    next_page_btn = pagination_element.find_element(
                        By.XPATH, f"//button[@aria-label='Page {current_page+1}']"
                    )
                    human_click(next_page_btn)
                    random_sleep(3, 6)
                    print_lg(f"\n>-> Now on Page {current_page+1} \n")
                except NoSuchElementException:
                    break

        except (NoSuchWindowException, WebDriverException) as e:
            raise e
        except Exception as e:
            print_lg("Failed to find Job listings!", e)

