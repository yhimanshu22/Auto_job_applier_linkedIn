import streamlit as st
import re
import os
import subprocess
import sys

st.set_page_config(page_title="LinkedIn Bot Config", layout="wide")

st.title("🤖 LinkedIn Bot Configuration")

CONFIG_DIR = "config"


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
        match = re.search(rf"{var_name}\s*=\s*(\d+)", content)
        return int(match.group(1)) if match else 0
    elif var_type == "list":
        match = re.search(rf"{var_name}\s*=\s*(\[.*?\])", content, re.DOTALL)
        if match:
            try:
                return eval(match.group(1))
            except:
                return []
        return []


tabs = st.tabs(["Personal Info", "Questions", "Search", "Settings", "Secrets"])

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

        years_of_experience = st.text_input(
            "Years of Experience",
            extract_value(content, "years_of_experience", "string"),
        )
        require_visa = st.selectbox(
            "Require Visa Sponsorship?",
            ["Yes", "No"],
            index=(
                ["Yes", "No"].index(extract_value(content, "require_visa", "string"))
                if extract_value(content, "require_visa", "string") in ["Yes", "No"]
                else 1
            ),
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

        desired_salary = st.number_input(
            "Desired Salary", value=extract_value(content, "desired_salary", "int")
        )
        notice_period = st.number_input(
            "Notice Period (days)", value=extract_value(content, "notice_period", "int")
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

        if st.button("Save Questions"):
            new_content = content
            new_content = update_variable(
                new_content, "years_of_experience", years_of_experience
            )
            new_content = update_variable(new_content, "require_visa", require_visa)
            new_content = update_variable(new_content, "us_citizenship", us_citizenship)
            new_content = update_variable(new_content, "desired_salary", desired_salary)
            new_content = update_variable(new_content, "notice_period", notice_period)
            new_content = update_variable(
                new_content, "linkedin_summary", linkedin_summary
            )
            new_content = update_variable(new_content, "cover_letter", cover_letter)
            new_content = update_variable(
                new_content, "user_information_all", user_information_all
            )
            save_file(filepath, new_content)
            st.success("Saved!")

# --- Search ---
with tabs[2]:
    st.header("Search Preferences")
    filepath = os.path.join(CONFIG_DIR, "search.py")
    if os.path.exists(filepath):
        content = read_file(filepath)

        search_location = st.text_input(
            "Search Location", extract_value(content, "search_location", "string")
        )

        # Lists are harder to edit with simple inputs, using text area for now or just display
        st.info(
            "For lists like 'search_terms', please edit the file directly for now to avoid formatting issues, or use the text area below carefully."
        )

        # Simple implementation for search_terms as comma separated string
        current_terms = extract_value(content, "search_terms", "list")
        search_terms_str = st.text_area(
            "Search Terms (format: ['Term1', 'Term2'])", str(current_terms)
        )

        easy_apply_only = st.checkbox(
            "Easy Apply Only", extract_value(content, "easy_apply_only", "bool")
        )

        if st.button("Save Search Preferences"):
            new_content = content
            new_content = update_variable(
                new_content, "search_location", search_location
            )
            new_content = update_variable(
                new_content, "easy_apply_only", easy_apply_only
            )

            # Try to update list
            try:
                new_list = eval(search_terms_str)
                if isinstance(new_list, list):
                    new_content = update_variable(new_content, "search_terms", new_list)
            except:
                st.error("Invalid list format for Search Terms")

            save_file(filepath, new_content)
            st.success("Saved!")

# --- Settings ---
with tabs[3]:
    st.header("Bot Settings")
    filepath = os.path.join(CONFIG_DIR, "settings.py")
    if os.path.exists(filepath):
        content = read_file(filepath)

        stealth_mode = st.checkbox(
            "Stealth Mode (Recommended)", extract_value(content, "stealth_mode", "bool")
        )
        safe_mode = st.checkbox(
            "Safe Mode (Use Guest Profile)", extract_value(content, "safe_mode", "bool")
        )
        run_in_background = st.checkbox(
            "Run in Background (Headless)",
            extract_value(content, "run_in_background", "bool"),
        )
        disable_extensions = st.checkbox(
            "Disable Extensions", extract_value(content, "disable_extensions", "bool")
        )

        if st.button("Save Settings"):
            new_content = content
            new_content = update_variable(new_content, "stealth_mode", stealth_mode)
            new_content = update_variable(new_content, "safe_mode", safe_mode)
            new_content = update_variable(
                new_content, "run_in_background", run_in_background
            )
            new_content = update_variable(
                new_content, "disable_extensions", disable_extensions
            )
            save_file(filepath, new_content)
            st.success("Saved!")

# --- Secrets ---
with tabs[4]:
    st.header("Secrets")
    filepath = os.path.join(CONFIG_DIR, "secrets.py")
    if os.path.exists(filepath):
        content = read_file(filepath)

        username = st.text_input(
            "LinkedIn Username", extract_value(content, "username", "string")
        )
        password = st.text_input(
            "LinkedIn Password",
            extract_value(content, "password", "string"),
            type="password",
        )

        llm_api_key = st.text_input(
            "LLM API Key",
            extract_value(content, "llm_api_key", "string"),
            type="password",
        )

        if st.button("Save Secrets"):
            new_content = content
            new_content = update_variable(new_content, "username", username)
            new_content = update_variable(new_content, "password", password)
            new_content = update_variable(new_content, "llm_api_key", llm_api_key)
            save_file(filepath, new_content)
            st.success("Saved!")

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
