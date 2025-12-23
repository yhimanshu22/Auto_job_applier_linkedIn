import streamlit as st
import re
import os
import subprocess
import sys
import pandas as pd
import json
import ast
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


# helper to load csv efficiently
def load_data(file_path):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            st.error(f"Error reading {file_path}: {e}")
            return None
    return None


def save_configuration(filepath, updates):
    """
    Reads the file, updates multiple variables, saves it, and shows a success message.
    updates: dict of {var_name: new_value}
    """
    if not os.path.exists(filepath):
        st.error(f"File not found: {filepath}")
        return

    try:
        content = read_file(filepath)
        for var_name, new_value in updates.items():
            content = update_variable(content, var_name, new_value)
        save_file(filepath, content)
        st.success(f"Saved changes to {os.path.basename(filepath)}!")
    except Exception as e:
        st.error(f"Failed to save {filepath}: {e}")


APPLIED_JOBS_FILE = "all excels/all_applied_applications_history.csv"
FAILED_JOBS_FILE = "all excels/all_failed_applications_history.csv"


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
            save_configuration(
                filepath,
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone_number": phone_number,
                    "current_city": current_city,
                    "country": country,
                    "ethnicity": ethnicity,
                    "gender": gender,
                },
            )

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
            save_configuration(
                filepath,
                {
                    "default_resume_path": default_resume_path,
                    "years_of_experience": years_of_experience,
                    "require_visa": require_visa,
                    "website": website,
                    "linkedIn": linkedIn,
                    "us_citizenship": us_citizenship,
                    "desired_salary": desired_salary,
                    "current_ctc": current_ctc,
                    "currency": currency,
                    "notice_period": notice_period,
                    "linkedin_headline": linkedin_headline,
                    "linkedin_summary": linkedin_summary,
                    "cover_letter": cover_letter,
                    "user_information_all": user_information_all,
                    "recent_employer": recent_employer,
                    "confidence_level": confidence_level,
                    "pause_before_submit": pause_before_submit,
                    "pause_at_failed_question": pause_at_failed_question,
                    "overwrite_previous_answers": overwrite_previous_answers,
                },
            )

        # Custom Answers from History
        st.subheader("Custom Answers from History")
        st.markdown(
            "Extract questions from your applied jobs history and define custom answers."
        )
        custom_qa_path = os.path.join(CONFIG_DIR, "custom_qa.json")

        # Load existing custom answers
        if os.path.exists(custom_qa_path):
            try:
                with open(custom_qa_path, "r", encoding="utf-8") as f:
                    custom_answers = json.load(f)
            except:
                custom_answers = {}
        else:
            custom_answers = {}

        # Parse CSV for unique questions
        df = load_data(APPLIED_JOBS_FILE)
        unique_questions = set()
        if df is not None and "Questions Found" in df.columns:
            for val in df["Questions Found"].dropna():
                try:
                    if isinstance(val, str):
                        qs = ast.literal_eval(val)
                        if isinstance(qs, (set, list)):
                            for q in qs:
                                if isinstance(q, tuple) and len(q) > 0:
                                    unique_questions.add(q[0])
                except Exception as e:
                    pass

        # Sort questions for consistent display
        sorted_questions = sorted(list(unique_questions))

        # UI for editing answers
        selected_question = st.selectbox(
            "Select a Question to Answer", ["Select..."] + sorted_questions
        )

        if selected_question != "Select...":
            current_ans = custom_answers.get(selected_question, "")
            new_ans = st.text_input(
                f"Answer for: {selected_question}", value=current_ans
            )

            if st.button("Save Answer"):
                custom_answers[selected_question] = new_ans
                with open(custom_qa_path, "w", encoding="utf-8") as f:
                    json.dump(custom_answers, f, indent=4)
                st.success(f"Saved answer for: {selected_question}")

        # Display existing custom answers
        if custom_answers:
            st.markdown("### Existing Custom Answers")
            for q, a in custom_answers.items():
                col_a, col_b = st.columns([0.8, 0.2])
                with col_a:
                    st.text_input(q, a, disabled=True, key=f"view_{q}")
                with col_b:
                    if st.button("Delete", key=f"del_{q}"):
                        del custom_answers[q]
                        with open(custom_qa_path, "w", encoding="utf-8") as f:
                            json.dump(custom_answers, f, indent=4)
                        st.rerun()

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
            try:
                # Prepare all updates
                updates = {
                    "search_location": search_location,
                    "switch_number": switch_number,
                    "randomize_search_order": randomize_search_order,
                    "pause_after_filters": pause_after_filters,
                    "sort_by": sort_by,
                    "easy_apply_only": easy_apply_only,
                    "date_posted": date_posted,
                    "under_10_applicants": under_10_applicants,
                    "salary": salary,
                    "in_your_network": in_your_network,
                    "fair_chance_employer": fair_chance_employer,
                    "experience_level": experience_level,
                    "job_type": job_type,
                    "on_site": on_site,
                    "security_clearance": security_clearance,
                    "did_masters": did_masters,
                    "current_experience": current_experience,
                }

                # Add complex lists
                new_terms = eval(search_terms_str)
                if isinstance(new_terms, list):
                    updates["search_terms"] = new_terms

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
                        updates[var_name] = new_list

                save_configuration(filepath, updates)
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
            save_configuration(
                filepath,
                {
                    "close_tabs": close_tabs,
                    "follow_companies": follow_companies,
                    "run_non_stop": run_non_stop,
                    "alternate_sortby": alternate_sortby,
                    "cycle_date_posted": cycle_date_posted,
                    "stop_date_cycle_at_24hr": stop_date_cycle_at_24hr,
                    "file_name": file_name,
                    "failed_file_name": failed_file_name,
                    "logs_folder_path": logs_folder_path,
                    "generated_resume_path": generated_resume_path,
                    "click_gap": click_gap,
                    "stealth_mode": stealth_mode,
                    "safe_mode": safe_mode,
                    "run_in_background": run_in_background,
                    "disable_extensions": disable_extensions,
                    "smooth_scroll": smooth_scroll,
                    "keep_screen_awake": keep_screen_awake,
                    "showAiErrorAlerts": showAiErrorAlerts,
                },
            )

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


def process_csv_dates(df, date_column, daily_stats_dict, metric_key):
    """
    Helper to process date columns from dataframe and update stats dict.
    """
    if df is not None and not df.empty and date_column in df.columns:
        # Convert to datetime, handling errors
        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
        # Group by date
        daily_counts = df.groupby(df[date_column].dt.date).size()
        for date_obj, count in daily_counts.items():
            date_str = str(date_obj)
            if date_str not in daily_stats_dict:
                daily_stats_dict[date_str] = {"Applied": 0, "Failed": 0}
            daily_stats_dict[date_str][metric_key] += int(count)


def get_stats_from_csvs():
    """
    Reads the CSV files to get daily counts for Applied and Failed jobs.
    Returns a dictionary keyed by date (YYYY-MM-DD).
    """
    daily_csv_stats = {}

    # 1. Process Applied Jobs
    df_applied = load_data(APPLIED_JOBS_FILE)
    process_csv_dates(df_applied, "Date Applied", daily_csv_stats, "Applied")

    # 2. Process Failed Jobs
    df_failed = load_data(FAILED_JOBS_FILE)
    process_csv_dates(df_failed, "Date Tried", daily_csv_stats, "Failed")

    return daily_csv_stats


def parse_log_metrics(log_path="logs/log.txt"):
    """
    Parses logs for 'External' and 'Skipped' only.
    'Applied' and 'Failed' are now fetched from CSVs for accuracy.
    """
    daily_log_stats = {}
    current_date = "Unknown"

    if not os.path.exists(log_path):
        return {}

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                # Check for Date
                date_match = re.search(r"Date and Time:\s+(\d{4}-\d{2}-\d{2})", line)
                if date_match:
                    current_date = date_match.group(1)

                if current_date == "Unknown":
                    continue

                if current_date not in daily_log_stats:
                    daily_log_stats[current_date] = {
                        "External": 0,
                        "Skipped": 0,
                    }

                # We only parse External and Skipped from logs now
                if "External job links collected:" in line:
                    match = re.search(r"External job links collected:\s+(\d+)", line)
                    if match:
                        daily_log_stats[current_date]["External"] += int(match.group(1))
                elif "Irrelevant jobs skipped:" in line:
                    match = re.search(r"Irrelevant jobs skipped:\s+(\d+)", line)
                    if match:
                        daily_log_stats[current_date]["Skipped"] += int(match.group(1))

        return daily_log_stats
    except Exception as e:
        st.sidebar.error(f"Error parsing log file: {e}")
        return {}


if st.sidebar.button("🔄 Refresh Stats"):
    st.rerun()

# --- Merge Data Sources ---
csv_stats = get_stats_from_csvs()
log_stats = parse_log_metrics()

# Create a master set of all dates
all_dates = sorted(set(csv_stats.keys()) | set(log_stats.keys()))

# Build the combined daily_stats dictionary
daily_stats = {}
for date in all_dates:
    daily_stats[date] = {
        "Applied": csv_stats.get(date, {}).get("Applied", 0),
        "Failed": csv_stats.get(date, {}).get("Failed", 0),
        "External": log_stats.get(date, {}).get("External", 0),
        "Skipped": log_stats.get(date, {}).get("Skipped", 0),
    }

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
    st.sidebar.info("No stats available.")
