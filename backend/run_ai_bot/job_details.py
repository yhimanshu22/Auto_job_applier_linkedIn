"""Job card extraction, blacklist, and description parsing."""

from typing import Literal

from run_ai_bot.bootstrap_env import *
from run_ai_bot.humanize import human_click
from run_ai_bot.session import log_to_db
from run_ai_bot.reporting import discard_job
from run_ai_bot.state import *


def get_job_main_details(
    job: WebElement, blacklisted_companies: set, rejected_jobs: set
) -> tuple[str, str, str, str, str, bool]:
    """
    # Function to get job main details.
    Returns a tuple of (job_id, title, company, work_location, work_style, skip)
    * job_id: Job ID
    * title: Job title
    * company: Company name
    * work_location: Work location of this job
    * work_style: Work style of this job (Remote, On-site, Hybrid)
    * skip: A boolean flag to skip this job
    """
    job_details_button = job.find_element(
        By.TAG_NAME, "a"
    )  # job.find_element(By.CLASS_NAME, "job-card-list__title")  # Problem in India
    scroll_to_view(driver, job_details_button, True)
    job_id = job.get_dom_attribute("data-occludable-job-id")
    title = job_details_button.text
    title = title[: title.find("\n")]
    # company = job.find_element(By.CLASS_NAME, "job-card-container__primary-description").text
    # work_location = job.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text
    other_details = job.find_element(
        By.CLASS_NAME, "artdeco-entity-lockup__subtitle"
    ).text
    index = other_details.find(" · ")
    company = other_details[:index]
    work_location = other_details[index + 3 :]
    work_style = work_location[work_location.rfind("(") + 1 : work_location.rfind(")")]
    work_location = work_location[: work_location.rfind("(")].strip()

    # Skip if previously rejected due to blacklist or already applied
    skip = False
    if company in blacklisted_companies:
        print_lg(
            f'Skipping "{title} | {company}" job (Blacklisted Company). Job ID: {job_id}!'
        )
        log_to_db(status="skipped", job_title=title, company=company, job_url=f"https://www.linkedin.com/jobs/view/{job_id}/", reason="Blacklisted Company")
        skip = True
    elif job_id in rejected_jobs:
        print_lg(
            f'Skipping previously rejected "{title} | {company}" job. Job ID: {job_id}!'
        )
        skip = True
    try:
        if (
            job.find_element(By.CLASS_NAME, "job-card-container__footer-job-state").text
            == "Applied"
        ):
            skip = True
            print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
    except:
        pass
    try:
        if not skip:
            # job_details_button.click()
            human_click(job_details_button)
    except Exception as e:
        print_lg(
            f'Failed to click "{title} | {company}" job on details button. Job ID: {job_id}!'
        )
        # print_lg(e)
        discard_job()
        job_details_button.click()  # To pass the error outside
    buffer(click_gap)
    return (job_id, title, company, work_location, work_style, skip)


# Function to check for Blacklisted words in About Company
def check_blacklist(
    rejected_jobs: set, job_id: str, company: str, blacklisted_companies: set
) -> tuple[set, set, WebElement] | ValueError:
    jobs_top_card = try_find_by_classes(
        driver,
        [
            "job-details-jobs-unified-top-card__primary-description-container",
            "job-details-jobs-unified-top-card__primary-description",
            "jobs-unified-top-card__primary-description",
            "jobs-details__main-content",
        ],
    )
    about_company_org = find_by_class(driver, "jobs-company__box")
    scroll_to_view(driver, about_company_org)
    about_company_org = about_company_org.text
    about_company = about_company_org.lower()
    skip_checking = False
    for word in about_company_good_words:
        if word.lower() in about_company:
            print_lg(
                f'Found the word "{word}". So, skipped checking for blacklist words.'
            )
            skip_checking = True
            break
    if not skip_checking:
        for word in about_company_bad_words:
            if word.lower() in about_company:
                rejected_jobs.add(job_id)
                blacklisted_companies.add(company)
                raise ValueError(f'\n"{about_company_org}"\n\nContains "{word}".')
    buffer(click_gap)
    scroll_to_view(driver, jobs_top_card)
    return rejected_jobs, blacklisted_companies, jobs_top_card


# Function to extract years of experience required from About Job
def extract_years_of_experience(text: str) -> int:
    # Extract all patterns like '10+ years', '5 years', '3-5 years', etc.
    matches = re.findall(re_experience, text)
    if len(matches) == 0:
        print_lg(f"\n{text}\n\nCouldn't find experience requirement in About the Job!")
        return 0
    return max([int(match) for match in matches if int(match) <= 12])


def get_job_description() -> (
    tuple[
        str | Literal["Unknown"], int | Literal["Unknown"], bool, str | None, str | None
    ]
):
    """
    # Job Description
    Function to extract job description from About the Job.
    ### Returns:
    - `jobDescription: str | 'Unknown'`
    - `experience_required: int | 'Unknown'`
    - `skip: bool`
    - `skipReason: str | None`
    - `skipMessage: str | None`
    """
    try:
        ##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------
        jobDescription = "Unknown"
        ##<
        experience_required = "Unknown"
        found_masters = 0
        jobDescription = find_by_class(driver, "jobs-box__html-content").text
        jobDescriptionLow = jobDescription.lower()
        skip = False
        skipReason = None
        skipMessage = None
        for word in bad_words:
            if word.lower() in jobDescriptionLow:
                skipMessage = f'\n{jobDescription}\n\nContains bad word "{word}". Skipping this job!\n'
                skipReason = "Found a Bad Word in About Job"
                skip = True
                break
        if (
            not skip
            and security_clearance == False
            and (
                "polygraph" in jobDescriptionLow
                or "clearance" in jobDescriptionLow
                or "secret" in jobDescriptionLow
            )
        ):
            skipMessage = f'\n{jobDescription}\n\nFound "Clearance" or "Polygraph". Skipping this job!\n'
            skipReason = "Asking for Security clearance"
            skip = True
        if not skip:
            if did_masters and "master" in jobDescriptionLow:
                print_lg(f'Found the word "master" in \n{jobDescription}')
                found_masters = 2
            experience_required = extract_years_of_experience(jobDescription)
            if (
                current_experience > -1
                and experience_required > current_experience + found_masters
            ):
                skipMessage = f"\n{jobDescription}\n\nExperience required {experience_required} > Current Experience {current_experience + found_masters}. Skipping this job!\n"
                skipReason = "Required experience is high"
                skip = True
    except Exception as e:
        if jobDescription == "Unknown":
            print_lg("Unable to extract job description!")
        else:
            experience_required = "Error in extraction"
            print_lg("Unable to extract years of experience required!")
            # print_lg(e)
    finally:
        if skip:
            log_to_db(status="skipped", reason=skipReason)
        return jobDescription, experience_required, skip, skipReason, skipMessage
