import streamlit as st
import re
import os
import subprocess
import sys
import pandas as pd
from dotenv import load_dotenv, set_key

st.set_page_config(page_title="LinkedIn Bot Config", layout="wide")

st.title("🤖 LinkedIn Bot Configuration")

CONFIG_DIR = "config"
ENV_FILE = ".env"

# Load environment variables
load_dotenv(ENV_FILE)


def read_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def save_file(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def update_variable(content, var_name, new_value):
    # Handle strings
    if isinstance(new_value, str):
        # Determine quote style based on content
        if "\n" in new_value or '"' in new_value or "'" in new_value:
            # Use triple double quotes for complex strings
            safe_value = new_value.replace('"""', '\\"\\"\\"')
            new_val_str = f'"""{safe_value}"""'
        else:
            # Use simple double quotes for simple strings
            safe_value = new_value.replace('"', '\\"')
            new_val_str = f'"{safe_value}"'

        # Regex to match existing string assignment (triple or single quotes)
        # Order matters: check triple quotes first!
        pattern = (
            rf'({var_name}\s*=\s*)(?:"""(.*?)"""|\'\'\'(.*?)\'\'\'|"(.*?)"|\'(.*?)\')'
        )

        # Use a function for replacement to avoid backslash escaping issues in re.sub
        def replacer(match):
            return f"{match.group(1)}{new_val_str}"

        return re.sub(pattern, replacer, content, flags=re.DOTALL)

    # Handle booleans
    elif isinstance(new_value, bool):
        pattern = rf"({var_name}\s*=\s*)(True|False)"

        def replacer(match):
            return f"{match.group(1)}{str(new_value)}"

        return re.sub(pattern, replacer, content)

    # Handle integers
    elif isinstance(new_value, int):
        pattern = rf"({var_name}\s*=\s*)(\d+)"

        def replacer(match):
            return f"{match.group(1)}{str(new_value)}"

        return re.sub(pattern, replacer, content)

    # Handle lists (simple implementation for list of strings)
    elif isinstance(new_value, list):
        list_str = str(new_value).replace("'", '"')  # Use double quotes
        pattern = rf"({var_name}\s*=\s*)(\[.*?\])"

        def replacer(match):
            return f"{match.group(1)}{list_str}"

        return re.sub(pattern, replacer, content, flags=re.DOTALL)

    return content


def extract_value(content, var_name, var_type):
    if var_type == "string":
        # Try matching triple double quotes first
        match = re.search(rf'{var_name}\s*=\s*"""(.*?)"""', content, re.DOTALL)
        if match:
            return match.group(1)

        # Try matching triple single quotes
        match = re.search(rf"{var_name}\s*=\s*'''(.*?)'''", content, re.DOTALL)
        if match:
            return match.group(1)

        # Try matching single double quotes
        match = re.search(rf'{var_name}\s*=\s*"(.*?)"', content)
        if match:
            return match.group(1)

        # Try matching single single quotes
        match = re.search(rf"{var_name}\s*=\s*'(.*?)'", content)
        if match:
            return match.group(1)

        return ""

    elif var_type == "bool":
        match = re.search(rf"{var_name}\s*=\s*(True|False)", content)
        return match.group(1) == "True" if match else False
    elif var_type == "int":
        match = re.search(rf"{var_name}\s*=\s*(-?\d+)", content)
        return int(match.group(1)) if match else 0
    elif var_type == "list":
        match = re.search(rf"{var_name}\s*=\s*(\[.*?\])", content, re.DOTALL)
        if match:
            try:
                return eval(match.group(1))
            except:
                return []
        return []


def update_env_var(key, value):
    # If value is boolean, convert to string
    if isinstance(value, bool):
        value = str(value)

    # Create .env if it doesn't exist
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w") as f:
            f.write("")

    set_key(ENV_FILE, key, str(value))
    os.environ[key] = str(value)  # Update current session as well


tabs = st.tabs(
    ["Personal Info", "Questions", "Search", "Settings", "Secrets", "Applications"]
)

# --- Personal Info ---
with tabs[0]:
    st.header("Personal Information")
    filepath = os.path.join(CONFIG_DIR, "personals.py")
    if os.path.exists(filepath):
        content = read_file(filepath)

        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input(
                "First Name", extract_value(content, "first_name", "string")
            )
            last_name = st.text_input(
                "Last Name", extract_value(content, "last_name", "string")
            )
            phone_number = st.text_input(
                "Phone Number", extract_value(content, "phone_number", "string")
            )

        with col2:
            current_city = st.text_input(
                "Current City", extract_value(content, "current_city", "string")
            )
            country = st.text_input(
                "Country", extract_value(content, "country", "string")
            )
            ethnicity = st.selectbox(
                "Ethnicity",
                [
                    "Decline",
                    "Hispanic/Latino",
                    "American Indian or Alaska Native",
                    "Asian",
                    "Black or African American",
                    "Native Hawaiian or Other Pacific Islander",
                    "White",
                    "Other",
                ],
                index=(
                    [
                        "Decline",
                        "Hispanic/Latino",
                        "American Indian or Alaska Native",
                        "Asian",
                        "Black or African American",
                        "Native Hawaiian or Other Pacific Islander",
                        "White",
                        "Other",
                    ].index(extract_value(content, "ethnicity", "string"))
                    if extract_value(content, "ethnicity", "string")
                    in [
                        "Decline",
                        "Hispanic/Latino",
                        "American Indian or Alaska Native",
                        "Asian",
                        "Black or African American",
                        "Native Hawaiian or Other Pacific Islander",
                        "White",
                        "Other",
                    ]
                    else 0
                ),
            )
            gender = st.selectbox(
                "Gender",
                ["Male", "Female", "Other", "Decline"],
                index=(
                    ["Male", "Female", "Other", "Decline"].index(
                        extract_value(content, "gender", "string")
                    )
                    if extract_value(content, "gender", "string")
                    in ["Male", "Female", "Other", "Decline"]
                    else 0
                ),
            )

        if st.button("Save Personal Info"):
            new_content = content
            new_content = update_variable(new_content, "first_name", first_name)
            new_content = update_variable(new_content, "last_name", last_name)
            new_content = update_variable(new_content, "phone_number", phone_number)
            new_content = update_variable(new_content, "current_city", current_city)
            new_content = update_variable(new_content, "country", country)
            new_content = update_variable(new_content, "ethnicity", ethnicity)
            new_content = update_variable(new_content, "gender", gender)
            save_file(filepath, new_content)
            st.success("Saved!")

# --- Questions ---
with tabs[1]:
    st.header("Application Questions")
    filepath = os.path.join(CONFIG_DIR, "questions.py")
    if os.path.exists(filepath):
        content = read_file(filepath)

        # Easy Apply Questions
        st.subheader("Easy Apply Questions")
        default_resume_path = st.text_input(
            "Default Resume Path",
            extract_value(content, "default_resume_path", "string"),
        )

        c1, c2 = st.columns(2)
        with c1:
            years_of_experience = st.text_input(
                "Years of Experience",
                extract_value(content, "years_of_experience", "string"),
            )
            require_visa = st.selectbox(
                "Require Visa Sponsorship?",
                ["Yes", "No"],
                index=(
                    ["Yes", "No"].index(
                        extract_value(content, "require_visa", "string")
                    )
                    if extract_value(content, "require_visa", "string") in ["Yes", "No"]
                    else 1
                ),
            )
            website = st.text_input(
                "Portfolio Website", extract_value(content, "website", "string")
            )
        with c2:
            linkedIn = st.text_input(
                "LinkedIn Profile URL", extract_value(content, "linkedIn", "string")
            )
            us_citizenship = st.selectbox(
                "US Citizenship Status",
                [
                    "U.S. Citizen/Permanent Resident",
                    "Non-citizen allowed to work for any employer",
                    "Non-citizen allowed to work for current employer",
                    "Non-citizen seeking work authorization",
                    "Canadian Citizen/Permanent Resident",
                    "Other",
                    "Decline",
                ],
                index=(
                    [
                        "U.S. Citizen/Permanent Resident",
                        "Non-citizen allowed to work for any employer",
                        "Non-citizen allowed to work for current employer",
                        "Non-citizen seeking work authorization",
                        "Canadian Citizen/Permanent Resident",
                        "Other",
                        "Decline",
                    ].index(extract_value(content, "us_citizenship", "string"))
                    if extract_value(content, "us_citizenship", "string")
                    in [
                        "U.S. Citizen/Permanent Resident",
                        "Non-citizen allowed to work for any employer",
                        "Non-citizen allowed to work for current employer",
                        "Non-citizen seeking work authorization",
                        "Canadian Citizen/Permanent Resident",
                        "Other",
                        "Decline",
                    ]
                    else 5
                ),
            )

        # Salary & Notice
        st.subheader("Salary & Notice Period")
        c3, c4 = st.columns(2)
        with c3:
            desired_salary = st.number_input(
                "Desired Salary", value=extract_value(content, "desired_salary", "int")
            )
            currency = st.text_input(
                "Currency", extract_value(content, "currency", "string")
            )
        with c4:
            current_ctc = st.number_input(
                "Current CTC", value=extract_value(content, "current_ctc", "int")
            )
            notice_period = st.number_input(
                "Notice Period (days)",
                value=extract_value(content, "notice_period", "int"),
            )

        # Profile Info
        st.subheader("Profile Information")
        linkedin_headline = st.text_input(
            "LinkedIn Headline", extract_value(content, "linkedin_headline", "string")
        )
        linkedin_summary = st.text_area(
            "LinkedIn Summary",
            extract_value(content, "linkedin_summary", "string"),
            height=150,
        )
        cover_letter = st.text_area(
            "Cover Letter", extract_value(content, "cover_letter", "string"), height=200
        )
        user_information_all = st.text_area(
            "User Information (for AI)",
            extract_value(content, "user_information_all", "string"),
            height=150,
        )

        # Misc
        st.subheader("Miscellaneous")
        recent_employer = st.text_input(
            "Recent Employer", extract_value(content, "recent_employer", "string")
        )
        confidence_level = st.text_input(
            "Confidence Level (1-10)",
            extract_value(content, "confidence_level", "string"),
        )

        # Related Settings
        st.subheader("Related Settings")
        pause_before_submit = st.checkbox(
            "Pause Before Submit", extract_value(content, "pause_before_submit", "bool")
        )
        pause_at_failed_question = st.checkbox(
            "Pause at Failed Question",
            extract_value(content, "pause_at_failed_question", "bool"),
        )
        overwrite_previous_answers = st.checkbox(
            "Overwrite Previous Answers",
            extract_value(content, "overwrite_previous_answers", "bool"),
        )

        if st.button("Save Questions"):
            new_content = content
            new_content = update_variable(
                new_content, "default_resume_path", default_resume_path
            )
            new_content = update_variable(
                new_content, "years_of_experience", years_of_experience
            )
            new_content = update_variable(new_content, "require_visa", require_visa)
            new_content = update_variable(new_content, "website", website)
            new_content = update_variable(new_content, "linkedIn", linkedIn)
            new_content = update_variable(new_content, "us_citizenship", us_citizenship)
            new_content = update_variable(new_content, "desired_salary", desired_salary)
            new_content = update_variable(new_content, "current_ctc", current_ctc)
            new_content = update_variable(new_content, "currency", currency)
            new_content = update_variable(new_content, "notice_period", notice_period)
            new_content = update_variable(
                new_content, "linkedin_headline", linkedin_headline
            )
            new_content = update_variable(
                new_content, "linkedin_summary", linkedin_summary
            )
            new_content = update_variable(new_content, "cover_letter", cover_letter)
            new_content = update_variable(
                new_content, "user_information_all", user_information_all
            )
            new_content = update_variable(
                new_content, "recent_employer", recent_employer
            )
            new_content = update_variable(
                new_content, "confidence_level", confidence_level
            )
            new_content = update_variable(
                new_content, "pause_before_submit", pause_before_submit
            )
            new_content = update_variable(
                new_content, "pause_at_failed_question", pause_at_failed_question
            )
            new_content = update_variable(
                new_content, "overwrite_previous_answers", overwrite_previous_answers
            )

            save_file(filepath, new_content)
            st.success("Saved!")

# --- Search ---
with tabs[2]:
    st.header("Search Preferences")
    filepath = os.path.join(CONFIG_DIR, "search.py")
    if os.path.exists(filepath):
        content = read_file(filepath)

        # 1. General Search Settings
        st.subheader("General Settings")
        col1, col2 = st.columns(2)
        with col1:
            search_location = st.text_input(
                "Search Location", extract_value(content, "search_location", "string")
            )
            switch_number = st.number_input(
                "Switch to next search after (applications)",
                value=extract_value(content, "switch_number", "int"),
                min_value=1,
            )
        with col2:
            randomize_search_order = st.checkbox(
                "Randomize Search Order",
                extract_value(content, "randomize_search_order", "bool"),
            )
            pause_after_filters = st.checkbox(
                "Pause after applying filters",
                extract_value(content, "pause_after_filters", "bool"),
            )

        st.info("Search Terms (Edit directly or use the text area below carefully)")
        current_terms = extract_value(content, "search_terms", "list")
        search_terms_str = st.text_area(
            "Search Terms (format: ['Term1', 'Term2'])", str(current_terms), height=100
        )

        # 2. Job Filters
        st.subheader("Job Filters")
        c1, c2, c3 = st.columns(3)
        with c1:
            sort_by = st.selectbox(
                "Sort By",
                ["", "Most recent", "Most relevant"],
                index=(
                    ["", "Most recent", "Most relevant"].index(
                        extract_value(content, "sort_by", "string")
                    )
                    if extract_value(content, "sort_by", "string")
                    in ["", "Most recent", "Most relevant"]
                    else 0
                ),
            )
            easy_apply_only = st.checkbox(
                "Easy Apply Only", extract_value(content, "easy_apply_only", "bool")
            )
        with c2:
            date_posted = st.selectbox(
                "Date Posted",
                ["", "Any time", "Past month", "Past week", "Past 24 hours"],
                index=(
                    ["", "Any time", "Past month", "Past week", "Past 24 hours"].index(
                        extract_value(content, "date_posted", "string")
                    )
                    if extract_value(content, "date_posted", "string")
                    in ["", "Any time", "Past month", "Past week", "Past 24 hours"]
                    else 0
                ),
            )
            under_10_applicants = st.checkbox(
                "Under 10 Applicants",
                extract_value(content, "under_10_applicants", "bool"),
            )
        with c3:
            salary = st.selectbox(
                "Salary",
                [
                    "",
                    "$40,000+",
                    "$60,000+",
                    "$80,000+",
                    "$100,000+",
                    "$120,000+",
                    "$140,000+",
                    "$160,000+",
                    "$180,000+",
                    "$200,000+",
                ],
                index=(
                    [
                        "",
                        "$40,000+",
                        "$60,000+",
                        "$80,000+",
                        "$100,000+",
                        "$120,000+",
                        "$140,000+",
                        "$160,000+",
                        "$180,000+",
                        "$200,000+",
                    ].index(extract_value(content, "salary", "string"))
                    if extract_value(content, "salary", "string")
                    in [
                        "",
                        "$40,000+",
                        "$60,000+",
                        "$80,000+",
                        "$100,000+",
                        "$120,000+",
                        "$140,000+",
                        "$160,000+",
                        "$180,000+",
                        "$200,000+",
                    ]
                    else 0
                ),
            )
            in_your_network = st.checkbox(
                "In Your Network", extract_value(content, "in_your_network", "bool")
            )
            fair_chance_employer = st.checkbox(
                "Fair Chance Employer",
                extract_value(content, "fair_chance_employer", "bool"),
            )

        # 3. Advanced Filters (Lists)
        st.subheader("Advanced Filters")

        # Experience Level
        exp_options = [
            "Internship",
            "Entry level",
            "Associate",
            "Mid-Senior level",
            "Director",
            "Executive",
        ]
        current_exp_level = extract_value(content, "experience_level", "list")
        experience_level = st.multiselect(
            "Experience Level",
            exp_options,
            default=[x for x in current_exp_level if x in exp_options],
        )

        # Job Type
        type_options = [
            "Full-time",
            "Part-time",
            "Contract",
            "Temporary",
            "Volunteer",
            "Internship",
            "Other",
        ]
        current_job_type = extract_value(content, "job_type", "list")
        job_type = st.multiselect(
            "Job Type",
            type_options,
            default=[x for x in current_job_type if x in type_options],
        )

        # On Site
        site_options = ["On-site", "Remote", "Hybrid"]
        current_on_site = extract_value(content, "on_site", "list")
        on_site = st.multiselect(
            "On-site/Remote",
            site_options,
            default=[x for x in current_on_site if x in site_options],
        )

        # 4. Dynamic Lists
        st.subheader("Dynamic Lists (Enter as Python lists)")
        with st.expander("Edit Dynamic Lists"):
            companies_str = st.text_area(
                "Companies", str(extract_value(content, "companies", "list"))
            )
            location_str = st.text_area(
                "Locations", str(extract_value(content, "location", "list"))
            )
            industry_str = st.text_area(
                "Industries", str(extract_value(content, "industry", "list"))
            )
            job_function_str = st.text_area(
                "Job Functions", str(extract_value(content, "job_function", "list"))
            )
            job_titles_str = st.text_area(
                "Job Titles", str(extract_value(content, "job_titles", "list"))
            )
            benefits_str = st.text_area(
                "Benefits", str(extract_value(content, "benefits", "list"))
            )
            commitments_str = st.text_area(
                "Commitments", str(extract_value(content, "commitments", "list"))
            )

        # 5. Exclusion/Inclusion Rules
        st.subheader("Exclusion Rules")
        about_company_bad_words_str = st.text_area(
            "About Company Bad Words",
            str(extract_value(content, "about_company_bad_words", "list")),
        )
        about_company_good_words_str = st.text_area(
            "About Company Good Words",
            str(extract_value(content, "about_company_good_words", "list")),
        )
        bad_words_str = st.text_area(
            "Job Description Bad Words",
            str(extract_value(content, "bad_words", "list")),
        )

        # 6. Experience & Qualifications
        st.subheader("Experience & Qualifications")
        qc1, qc2 = st.columns(2)
        with qc1:
            security_clearance = st.checkbox(
                "Security Clearance",
                extract_value(content, "security_clearance", "bool"),
            )
            did_masters = st.checkbox(
                "Masters Degree", extract_value(content, "did_masters", "bool")
            )
        with qc2:
            current_experience = st.number_input(
                "Current Experience (Years, -1 to ignore)",
                value=extract_value(content, "current_experience", "int"),
                min_value=-1,
            )

        if st.button("Save Search Preferences"):
            new_content = content
            # General
            new_content = update_variable(
                new_content, "search_location", search_location
            )
            new_content = update_variable(new_content, "switch_number", switch_number)
            new_content = update_variable(
                new_content, "randomize_search_order", randomize_search_order
            )
            new_content = update_variable(
                new_content, "pause_after_filters", pause_after_filters
            )

            # Filters
            new_content = update_variable(new_content, "sort_by", sort_by)
            new_content = update_variable(
                new_content, "easy_apply_only", easy_apply_only
            )
            new_content = update_variable(new_content, "date_posted", date_posted)
            new_content = update_variable(
                new_content, "under_10_applicants", under_10_applicants
            )
            new_content = update_variable(new_content, "salary", salary)
            new_content = update_variable(
                new_content, "in_your_network", in_your_network
            )
            new_content = update_variable(
                new_content, "fair_chance_employer", fair_chance_employer
            )

            # Advanced Filters
            new_content = update_variable(
                new_content, "experience_level", experience_level
            )
            new_content = update_variable(new_content, "job_type", job_type)
            new_content = update_variable(new_content, "on_site", on_site)

            # Qualifications
            new_content = update_variable(
                new_content, "security_clearance", security_clearance
            )
            new_content = update_variable(new_content, "did_masters", did_masters)
            new_content = update_variable(
                new_content, "current_experience", current_experience
            )

            # Lists
            try:
                # Search Terms
                new_terms = eval(search_terms_str)
                if isinstance(new_terms, list):
                    new_content = update_variable(
                        new_content, "search_terms", new_terms
                    )

                # Dynamic Lists
                for var_name, var_str in [
                    ("companies", companies_str),
                    ("location", location_str),
                    ("industry", industry_str),
                    ("job_function", job_function_str),
                    ("job_titles", job_titles_str),
                    ("benefits", benefits_str),
                    ("commitments", commitments_str),
                    ("about_company_bad_words", about_company_bad_words_str),
                    ("about_company_good_words", about_company_good_words_str),
                    ("bad_words", bad_words_str),
                ]:
                    new_list = eval(var_str)
                    if isinstance(new_list, list):
                        new_content = update_variable(new_content, var_name, new_list)

                save_file(filepath, new_content)
                st.success("Saved!")
            except Exception as e:
                st.error(f"Error saving lists: {e}. Please check your list formatting.")

# --- Settings ---
with tabs[3]:
    st.header("Bot Settings")
    filepath = os.path.join(CONFIG_DIR, "settings.py")
    if os.path.exists(filepath):
        content = read_file(filepath)

        # LinkedIn Settings
        st.subheader("LinkedIn Settings")
        col1, col2 = st.columns(2)
        with col1:
            close_tabs = st.checkbox(
                "Close External Tabs", extract_value(content, "close_tabs", "bool")
            )
            follow_companies = st.checkbox(
                "Follow Companies", extract_value(content, "follow_companies", "bool")
            )
            run_non_stop = st.checkbox(
                "Run Non-Stop (Beta)", extract_value(content, "run_non_stop", "bool")
            )
        with col2:
            alternate_sortby = st.checkbox(
                "Alternate Sort By", extract_value(content, "alternate_sortby", "bool")
            )
            cycle_date_posted = st.checkbox(
                "Cycle Date Posted", extract_value(content, "cycle_date_posted", "bool")
            )
            stop_date_cycle_at_24hr = st.checkbox(
                "Stop Date Cycle at 24hr",
                extract_value(content, "stop_date_cycle_at_24hr", "bool"),
            )

        # Global Settings
        st.subheader("Global Settings")

        # Paths
        st.markdown("##### File Paths")
        file_name = st.text_input(
            "Applied Jobs File", extract_value(content, "file_name", "string")
        )
        failed_file_name = st.text_input(
            "Failed Jobs File", extract_value(content, "failed_file_name", "string")
        )
        logs_folder_path = st.text_input(
            "Logs Folder", extract_value(content, "logs_folder_path", "string")
        )
        generated_resume_path = st.text_input(
            "Generated Resumes Path",
            extract_value(content, "generated_resume_path", "string"),
        )

        # Behavior
        st.markdown("##### Behavior")
        click_gap = st.number_input(
            "Click Gap (seconds)",
            value=extract_value(content, "click_gap", "int"),
            min_value=0,
        )

        c1, c2 = st.columns(2)
        with c1:
            stealth_mode = st.checkbox(
                "Stealth Mode (Recommended)",
                extract_value(content, "stealth_mode", "bool"),
            )
            safe_mode = st.checkbox(
                "Safe Mode (Guest Profile)", extract_value(content, "safe_mode", "bool")
            )
            run_in_background = st.checkbox(
                "Run in Background (Headless)",
                extract_value(content, "run_in_background", "bool"),
            )
        with c2:
            disable_extensions = st.checkbox(
                "Disable Extensions",
                extract_value(content, "disable_extensions", "bool"),
            )
            smooth_scroll = st.checkbox(
                "Smooth Scroll", extract_value(content, "smooth_scroll", "bool")
            )
            keep_screen_awake = st.checkbox(
                "Keep Screen Awake", extract_value(content, "keep_screen_awake", "bool")
            )
            showAiErrorAlerts = st.checkbox(
                "Show AI Error Alerts",
                extract_value(content, "showAiErrorAlerts", "bool"),
            )

# --- Applications ---
with tabs[5]:
    st.header("Job Application History")

    # helper to load csv efficiently
    def load_data(file_path):
        if os.path.exists(file_path):
            try:
                return pd.read_csv(file_path)
            except Exception as e:
                st.error(f"Error reading {file_path}: {e}")
                return None
        return None

    APPLIED_JOBS_FILE = "all excels/all_applied_applications_history.csv"
    FAILED_JOBS_FILE = "all excels/all_failed_applications_history.csv"

    st.subheader("Successfully Applied Jobs")
    df_applied = load_data(APPLIED_JOBS_FILE)
    if df_applied is not None and not df_applied.empty:
        st.dataframe(
            df_applied,
            width="stretch",
            column_config={
                "Job Link": st.column_config.LinkColumn("Job Link"),
                "HR Link": st.column_config.LinkColumn("HR Link"),
                "External Job link": st.column_config.LinkColumn("External Link"),
                "Date Applied": st.column_config.DatetimeColumn(
                    "Date Applied", format="D MMM YYYY, h:mm a"
                ),
            },
            hide_index=True,
        )
        st.caption(f"Total Applied: {len(df_applied)}")
    else:
        st.info("No applied jobs history found.")

    st.divider()

    st.subheader("Failed Applications")
    df_failed = load_data(FAILED_JOBS_FILE)
    if df_failed is not None and not df_failed.empty:
        st.dataframe(
            df_failed,
            width="stretch",
            column_config={
                "Job Link": st.column_config.LinkColumn("Job Link"),
                "External Job link": st.column_config.LinkColumn("External Link"),
                "Date Tried": st.column_config.DatetimeColumn(
                    "Date Tried", format="D MMM YYYY, h:mm a"
                ),
            },
            hide_index=True,
        )
        st.caption(f"Total Failed: {len(df_failed)}")
    else:
        st.info("No failed applications history found.")

        if st.button("Save Settings"):
            new_content = content
            # LinkedIn
            new_content = update_variable(new_content, "close_tabs", close_tabs)
            new_content = update_variable(
                new_content, "follow_companies", follow_companies
            )
            new_content = update_variable(new_content, "run_non_stop", run_non_stop)
            new_content = update_variable(
                new_content, "alternate_sortby", alternate_sortby
            )
            new_content = update_variable(
                new_content, "cycle_date_posted", cycle_date_posted
            )
            new_content = update_variable(
                new_content, "stop_date_cycle_at_24hr", stop_date_cycle_at_24hr
            )

            # Global
            new_content = update_variable(new_content, "file_name", file_name)
            new_content = update_variable(
                new_content, "failed_file_name", failed_file_name
            )
            new_content = update_variable(
                new_content, "logs_folder_path", logs_folder_path
            )
            new_content = update_variable(
                new_content, "generated_resume_path", generated_resume_path
            )
            new_content = update_variable(new_content, "click_gap", click_gap)
            new_content = update_variable(new_content, "stealth_mode", stealth_mode)
            new_content = update_variable(new_content, "safe_mode", safe_mode)
            new_content = update_variable(
                new_content, "run_in_background", run_in_background
            )
            new_content = update_variable(
                new_content, "disable_extensions", disable_extensions
            )
            new_content = update_variable(new_content, "smooth_scroll", smooth_scroll)
            new_content = update_variable(
                new_content, "keep_screen_awake", keep_screen_awake
            )
            new_content = update_variable(
                new_content, "showAiErrorAlerts", showAiErrorAlerts
            )

            save_file(filepath, new_content)
            st.success("Saved!")

# --- Secrets ---
with tabs[4]:
    st.header("Secrets")
    st.info("Secrets are now stored in a .env file for security.")

    # Read from environment variables (loaded by python-dotenv)
    current_username = os.getenv("LINKEDIN_USERNAME", "")
    current_password = os.getenv("LINKEDIN_PASSWORD", "")
    current_use_ai = os.getenv("USE_AI", "False") == "True"
    current_ai_provider = os.getenv("AI_PROVIDER", "openai")
    current_llm_api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/")
    current_llm_api_key = os.getenv("LLM_API_KEY", "not-needed")
    current_llm_model = os.getenv("LLM_MODEL", "gpt-5-mini")
    current_llm_spec = os.getenv("LLM_SPEC", "openai")
    current_stream_output = os.getenv("STREAM_OUTPUT", "False") == "True"

    st.subheader("LinkedIn Credentials")
    username = st.text_input("LinkedIn Username", current_username)
    password = st.text_input("LinkedIn Password", current_password, type="password")

    st.subheader("AI Configuration")
    use_AI = st.checkbox("Use AI", current_use_ai)

    if use_AI:
        ai_provider = st.selectbox(
            "AI Provider",
            ["openai", "deepseek", "gemini"],
            index=(
                ["openai", "deepseek", "gemini"].index(current_ai_provider)
                if current_ai_provider in ["openai", "deepseek", "gemini"]
                else 0
            ),
        )

        llm_api_url = st.text_input("LLM API URL", current_llm_api_url)
        llm_api_key = st.text_input("LLM API Key", current_llm_api_key, type="password")
        llm_model = st.text_input("LLM Model Name", current_llm_model)

        llm_spec = st.selectbox(
            "LLM Spec",
            ["openai", "openai-like", "openai-like-github", "openai-like-mistral"],
            index=(
                [
                    "openai",
                    "openai-like",
                    "openai-like-github",
                    "openai-like-mistral",
                ].index(current_llm_spec)
                if current_llm_spec
                in [
                    "openai",
                    "openai-like",
                    "openai-like-github",
                    "openai-like-mistral",
                ]
                else 0
            ),
        )

        stream_output = st.checkbox("Stream Output", current_stream_output)
    else:
        # Keep existing values if hidden
        ai_provider = current_ai_provider
        llm_api_url = current_llm_api_url
        llm_api_key = current_llm_api_key
        llm_model = current_llm_model
        llm_spec = current_llm_spec
        stream_output = current_stream_output

    if st.button("Save Secrets"):
        try:
            update_env_var("LINKEDIN_USERNAME", username)
            update_env_var("LINKEDIN_PASSWORD", password)
            update_env_var("USE_AI", use_AI)
            update_env_var("AI_PROVIDER", ai_provider)
            update_env_var("LLM_API_URL", llm_api_url)
            update_env_var("LLM_API_KEY", llm_api_key)
            update_env_var("LLM_MODEL", llm_model)
            update_env_var("LLM_SPEC", llm_spec)
            update_env_var("STREAM_OUTPUT", stream_output)
            st.success("Secrets saved to .env file!")
        except Exception as e:
            st.error(f"Failed to save secrets: {e}")

# --- Sidebar ---
st.sidebar.header("🤖 Bot Control")

PID_FILE = "bot_pid.txt"

if st.sidebar.button("🚀 Run Bot"):
    # Use sys.executable to ensure we use the same python interpreter
    try:
        # Run in a separate process so it doesn't block the UI completely
        # We use Popen to let it run independently
        process = subprocess.Popen(
            [sys.executable, "runAiBot.py"],
            cwd=os.getcwd(),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        # Save PID to file
        with open(PID_FILE, "w") as f:
            f.write(str(process.pid))

        st.sidebar.success(f"Bot started in a new console window! (PID: {process.pid})")
    except Exception as e:
        st.sidebar.error(f"Failed to start bot: {e}")

if st.sidebar.button("🛑 Stop Bot"):
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())

            # Use taskkill to kill the process tree
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid), "/T"],
                check=True,
                capture_output=True,
            )

            os.remove(PID_FILE)
            st.sidebar.success("Bot stopped successfully!")
        except subprocess.CalledProcessError:
            st.sidebar.warning(
                "Bot process not found (maybe already closed?). Cleaning up."
            )
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except Exception as e:
            st.sidebar.error(f"Failed to stop bot: {e}")
    else:
        st.sidebar.warning("No running bot found (PID file missing).")

# --- Bot Statistics ---
st.sidebar.markdown("---")
st.sidebar.header("📊 Bot Statistics")


def parse_log_metrics(log_path="logs/log.txt"):
    daily_stats = {}
    current_date = "Unknown"

    if not os.path.exists(log_path):
        return {}

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                # Check for Date
                # Format: Date and Time: 2025-12-14 12:50:45.882008
                date_match = re.search(r"Date and Time:\s+(\d{4}-\d{2}-\d{2})", line)
                if date_match:
                    current_date = date_match.group(1)
                    if current_date not in daily_stats:
                        daily_stats[current_date] = {
                            "Applied": 0,
                            "External": 0,
                            "Failed": 0,
                            "Skipped": 0,
                        }

                # Check for Metrics
                # Only count if we have a valid date (or assign to "Unknown")
                if current_date not in daily_stats:
                    daily_stats[current_date] = {
                        "Applied": 0,
                        "External": 0,
                        "Failed": 0,
                        "Skipped": 0,
                    }

                if "Jobs Easy Applied:" in line:
                    match = re.search(r"Jobs Easy Applied:\s+(\d+)", line)
                    if match:
                        daily_stats[current_date]["Applied"] += int(match.group(1))
                elif "External job links collected:" in line:
                    match = re.search(r"External job links collected:\s+(\d+)", line)
                    if match:
                        daily_stats[current_date]["External"] += int(match.group(1))
                elif "Failed jobs:" in line:
                    match = re.search(r"Failed jobs:\s+(\d+)", line)
                    if match:
                        daily_stats[current_date]["Failed"] += int(match.group(1))
                elif "Irrelevant jobs skipped:" in line:
                    match = re.search(r"Irrelevant jobs skipped:\s+(\d+)", line)
                    if match:
                        daily_stats[current_date]["Skipped"] += int(match.group(1))

        return daily_stats
    except Exception as e:
        st.sidebar.error(f"Error parsing log file: {e}")
        return {}


if st.sidebar.button("🔄 Refresh Stats"):
    st.rerun()

daily_stats = parse_log_metrics()

if daily_stats:
    # Calculate Grand Totals
    total_applied = sum(d["Applied"] for d in daily_stats.values())
    total_external = sum(d["External"] for d in daily_stats.values())
    total_failed = sum(d["Failed"] for d in daily_stats.values())
    total_skipped = sum(d["Skipped"] for d in daily_stats.values())

    # Display Grand Totals
    c1, c2 = st.sidebar.columns(2)
    c1.metric("Total Applied", total_applied)
    c2.metric("Total External", total_external)
    c3, c4 = st.sidebar.columns(2)
    c3.metric("Total Failed", total_failed)
    c4.metric("Total Skipped", total_skipped)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Daily Breakdown")

    # Prepare data for chart
    # Streamlit bar_chart expects a DataFrame or a dict where keys are x-axis labels
    # We want dates on x-axis, and bars for each metric.
    # Format: {"Date": ["2025-12-14"], "Applied": [10], "Failed": [2], ...}

    chart_data = {
        "Date": [],
        "Applied": [],
        "External": [],
        "Failed": [],
        "Skipped": [],
    }

    # Sort dates
    sorted_dates = sorted(daily_stats.keys())

    for date in sorted_dates:
        stats = daily_stats[date]
        chart_data["Date"].append(date)
        chart_data["Applied"].append(stats["Applied"])
        chart_data["External"].append(stats["External"])
        chart_data["Failed"].append(stats["Failed"])
        chart_data["Skipped"].append(stats["Skipped"])

    # Display Chart
    st.sidebar.bar_chart(
        data=chart_data,
        x="Date",
        y=["Applied", "External", "Failed", "Skipped"],
        stack=False,
    )

    # Display Table (optional, maybe in an expander)
    with st.sidebar.expander("Show Detailed Data"):
        st.dataframe(chart_data)

else:
    st.sidebar.info("No logs found or empty log file.")
