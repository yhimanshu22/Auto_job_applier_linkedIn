"""Easy Apply form: resume upload and question answering."""

from run_ai_bot.bootstrap_env import *
from run_ai_bot.session import log_to_db
from run_ai_bot.state import *

def upload_resume(modal: WebElement, resume: str) -> tuple[bool, str]:
    try:
        # 1. Attempt to get default resume metadata from database
        resumes = db.get_user_resumes(user_id)
        default_resume = next((r for r in resumes if r['is_default']), None)
        
        if default_resume:
            print_lg(f"Fetching default resume: {default_resume['file_name']} from storage...")
            file_content = storage_service.get_file_content(default_resume['storage_path'])
            
            if file_content:
                # Create a localized temporary file for Selenium to pick up
                # Note: This is necessary because Selenium's send_keys requires a local file path
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(file_content)
                    tmp_path = tmp.name
                
                print_lg(f"Uploading resume: {default_resume['file_name']}")
                modal.find_element(By.NAME, "file").send_keys(tmp_path)
                return True, default_resume["file_name"]

        # 2. Legacy Fallback: Try the Asset BLOB (backwards compatibility)
        asset = db.get_asset("default_resume")
        if asset:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(asset["content"])
                tmp_path = tmp.name
            print_lg(f"Uploading resume from database asset: {asset['filename']}")
            modal.find_element(By.NAME, "file").send_keys(tmp_path)
            return True, asset["filename"]
            
        # 3. Last Resort: Local file path
        if os.path.exists(resume):
            modal.find_element(By.NAME, "file").send_keys(os.path.abspath(resume))
            return True, os.path.basename(resume)
            
        return False, "Previous resume"
    except Exception as e:
        print_lg(f"Resume upload failed: {e}")
        return False, "Previous resume"


# Function to answer common questions for Easy Apply
def answer_common_questions(label: str, answer: str) -> str:
    if "sponsorship" in label or "visa" in label:
        answer = require_visa
    return answer


# Function to answer the questions for Easy Apply
def answer_questions(
    modal: WebElement,
    questions_list: set,
    work_location: str,
    job_description: str | None = None,
) -> set:
    custom_qa = {}
    custom_qa_path = "config/custom_qa.json"
    if os.path.exists(custom_qa_path):
        try:
            with open(custom_qa_path, "r", encoding="utf-8") as f:
                custom_qa = json.load(f)
        except:
            pass
    # Get all questions from the page

    all_questions = modal.find_elements(By.XPATH, ".//div[@data-test-form-element]")
    # all_questions = modal.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-element")
    # all_list_questions = modal.find_elements(By.XPATH, ".//div[@data-test-text-entity-list-form-component]")
    # all_single_line_questions = modal.find_elements(By.XPATH, ".//div[@data-test-single-line-text-form-component]")
    # all_questions = all_questions + all_list_questions + all_single_line_questions

    for Question in all_questions:
        # Check if it's a select Question
        select = try_xp(Question, ".//select", False)
        if select:
            label_org = "Unknown"
            try:
                label = Question.find_element(By.TAG_NAME, "label")
                label_org = label.find_element(By.TAG_NAME, "span").text
            except:
                pass
            answer = "Yes"
            label = label_org.lower()
            select = Select(select)
            selected_option = select.first_selected_option.text
            optionsText = []
            options = '"List of phone country codes"'
            if label != "phone country code":
                optionsText = [option.text for option in select.options]
                options = "".join([f' "{option}",' for option in optionsText])
            prev_answer = selected_option
            if overwrite_previous_answers or selected_option == "Select an option":
                ##> ------ WINDY_WINDWARD Email:karthik.sarode23@gmail.com - Added fuzzy logic to answer location based questions ------
                custom_key = f"{label_org} [ {options} ]"
                if custom_key in custom_qa:
                    answer = custom_qa[custom_key]
                elif "email" in label or "phone" in label:
                    answer = prev_answer
                elif "gender" in label or "sex" in label:
                    answer = gender
                elif "disability" in label:
                    answer = disability_status
                elif "proficiency" in label:
                    answer = "Professional"
                # Add location handling
                elif any(
                    loc_word in label
                    for loc_word in ["location", "city", "state", "country"]
                ):
                    if "country" in label:
                        answer = country
                    elif "state" in label:
                        answer = state
                    elif "city" in label:
                        answer = current_city if current_city else work_location
                    else:
                        answer = work_location
                else:
                    answer = answer_common_questions(label, answer)
                try:
                    select.select_by_visible_text(answer)
                except NoSuchElementException as e:
                    # Define similar phrases for common answers
                    possible_answer_phrases = []
                    if answer == "Decline":
                        possible_answer_phrases = [
                            "Decline",
                            "not wish",
                            "don't wish",
                            "Prefer not",
                            "not want",
                        ]
                    elif "yes" in answer.lower():
                        possible_answer_phrases = ["Yes", "Agree", "I do", "I have"]
                    elif "no" in answer.lower():
                        possible_answer_phrases = [
                            "No",
                            "Disagree",
                            "I don't",
                            "I do not",
                        ]
                    else:
                        # Try partial matching for any answer
                        possible_answer_phrases = [answer]
                        # Add lowercase and uppercase variants
                        possible_answer_phrases.append(answer.lower())
                        possible_answer_phrases.append(answer.upper())
                        # Try without special characters
                        possible_answer_phrases.append(
                            "".join(c for c in answer if c.isalnum())
                        )
                    ##<
                    foundOption = False
                    for phrase in possible_answer_phrases:
                        for option in optionsText:
                            # Check if phrase is in option or option is in phrase (bidirectional matching)
                            if (
                                phrase.lower() in option.lower()
                                or option.lower() in phrase.lower()
                            ):
                                select.select_by_visible_text(option)
                                answer = option
                                foundOption = True
                                break
                    if not foundOption:
                        # TODO: Use AI to answer the question need to be implemented logic to extract the options for the question
                        print_lg(
                            f'Failed to find an option with text "{answer}" for question labelled "{label_org}", answering randomly!'
                        )
                        select.select_by_index(randint(1, len(select.options) - 1))
                        answer = select.first_selected_option.text
                        randomly_answered_questions.add(
                            (f"{label_org} [ {options} ]", "select")
                        )
            questions_list.add(
                (f"{label_org} [ {options} ]", answer, "select", prev_answer)
            )
            continue

        # Check if it's a radio Question
        radio = try_xp(
            Question,
            './/fieldset[@data-test-form-builder-radio-button-form-component="true"]',
            False,
        )
        if radio:
            prev_answer = None
            label = try_xp(
                radio,
                ".//span[@data-test-form-builder-radio-button-form-component__title]",
                False,
            )
            try:
                label = find_by_class(label, "visually-hidden", 2.0)
            except:
                pass
            label_org = label.text if label else "Unknown"
            answer = "Yes"
            label = label_org.lower()

            label_org += " [ "
            options = radio.find_elements(By.TAG_NAME, "input")
            options_labels = []

            for option in options:
                id = option.get_attribute("id")
                option_label = try_xp(radio, f'.//label[@for="{id}"]', False)
                options_labels.append(
                    f'"{option_label.text if option_label else "Unknown"}"<{option.get_attribute("value")}>'
                )  # Saving option as "label <value>"
                if option.is_selected():
                    prev_answer = options_labels[-1]
                label_org += f" {options_labels[-1]},"

            if overwrite_previous_answers or prev_answer is None:
                custom_key = label_org + " ]"
                if custom_key in custom_qa:
                    answer = custom_qa[custom_key]
                elif "citizenship" in label or "employment eligibility" in label:
                    answer = us_citizenship
                elif "veteran" in label or "protected" in label:
                    answer = veteran_status
                elif "disability" in label or "handicapped" in label:
                    answer = disability_status
                else:
                    answer = answer_common_questions(label, answer)
                foundOption = try_xp(
                    radio, f".//label[normalize-space()='{answer}']", False
                )
                if foundOption:
                    actions.move_to_element(foundOption).click().perform()
                else:
                    possible_answer_phrases = (
                        ["Decline", "not wish", "don't wish", "Prefer not", "not want"]
                        if answer == "Decline"
                        else [answer]
                    )
                    ele = options[0]
                    answer = options_labels[0]
                    for phrase in possible_answer_phrases:
                        for i, option_label in enumerate(options_labels):
                            if phrase in option_label:
                                foundOption = options[i]
                                ele = foundOption
                                answer = (
                                    f"Decline ({option_label})"
                                    if len(possible_answer_phrases) > 1
                                    else option_label
                                )
                                break
                        if foundOption:
                            break
                    # if answer == 'Decline':
                    #     answer = options_labels[0]
                    #     for phrase in ["Prefer not", "not want", "not wish"]:
                    #         foundOption = try_xp(radio, f".//label[normalize-space()='{phrase}']", False)
                    #         if foundOption:
                    #             answer = f'Decline ({phrase})'
                    #             ele = foundOption
                    #             break
                    actions.move_to_element(ele).click().perform()
                    if not foundOption:
                        randomly_answered_questions.add((f"{label_org} ]", "radio"))
            else:
                answer = prev_answer
            questions_list.add((label_org + " ]", answer, "radio", prev_answer))
            continue

        # Check if it's a text question
        text = try_xp(Question, ".//input[@type='text']", False)
        if text:
            do_actions = False
            label = try_xp(Question, ".//label[@for]", False)
            try:
                label = label.find_element(By.CLASS_NAME, "visually-hidden")
            except:
                pass
            label_org = label.text if label else "Unknown"
            answer = ""  # years_of_experience
            label = label_org.lower()

            prev_answer = text.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if label_org in custom_qa:
                    answer = custom_qa[label_org]
                elif "experience" in label or "years" in label:
                    answer = years_of_experience
                elif "phone" in label or "mobile" in label:
                    answer = phone_number
                elif "street" in label:
                    answer = street
                elif "city" in label or "location" in label or "address" in label:
                    answer = current_city if current_city else work_location
                    do_actions = True
                elif "signature" in label:
                    answer = full_name  # 'signature' in label or 'legal name' in label or 'your name' in label or 'full name' in label: answer = full_name     # What if question is 'name of the city or university you attend, name of referral etc?'
                elif "name" in label:
                    if "full" in label:
                        answer = full_name
                    elif "first" in label and "last" not in label:
                        answer = first_name
                    elif "middle" in label and "last" not in label:
                        answer = middle_name
                    elif "last" in label and "first" not in label:
                        answer = last_name
                    elif "employer" in label:
                        answer = recent_employer
                    else:
                        answer = full_name
                elif "notice" in label:
                    if "month" in label:
                        answer = notice_period_months
                    elif "week" in label:
                        answer = notice_period_weeks
                    else:
                        answer = notice_period
                elif (
                    "salary" in label
                    or "compensation" in label
                    or "ctc" in label
                    or "pay" in label
                ):
                    if "current" in label or "present" in label:
                        if "month" in label:
                            answer = current_ctc_monthly
                        elif "lakh" in label:
                            answer = current_ctc_lakhs
                        else:
                            answer = current_ctc
                    else:
                        if "month" in label:
                            answer = desired_salary_monthly
                        elif "lakh" in label:
                            answer = desired_salary_lakhs
                        else:
                            answer = desired_salary
                elif "linkedin" in label:
                    answer = linkedIn
                elif (
                    "website" in label
                    or "blog" in label
                    or "portfolio" in label
                    or "link" in label
                ):
                    answer = website
                elif "scale of 1-10" in label:
                    answer = confidence_level
                elif "headline" in label:
                    answer = linkedin_headline
                elif (
                    ("hear" in label or "come across" in label)
                    and "this" in label
                    and ("job" in label or "position" in label)
                ):
                    answer = "https://github.com/GodsScion/Auto_job_applier_linkedIn"
                elif "state" in label or "province" in label:
                    answer = state
                elif "zip" in label or "postal" in label or "code" in label:
                    answer = zipcode
                elif "country" in label:
                    answer = country
                else:
                    answer = answer_common_questions(label, answer)
                ##> ------ Yang Li : MARKYangL - Feature ------
                if answer == "":
                    if use_AI and aiClient:
                        try:
                            if ai_provider.lower() == "openai":
                                answer = ai_answer_question(
                                    aiClient,
                                    label_org,
                                    question_type="text",
                                    job_description=job_description,
                                    user_information_all=user_information_all,
                                )
                            elif ai_provider.lower() == "deepseek":
                                answer = deepseek_answer_question(
                                    aiClient,
                                    label_org,
                                    options=None,
                                    question_type="text",
                                    job_description=job_description,
                                    about_company=None,
                                    user_information_all=user_information_all,
                                )
                            elif ai_provider.lower() == "gemini":
                                answer = gemini_answer_question(
                                    aiClient,
                                    label_org,
                                    options=None,
                                    question_type="text",
                                    job_description=job_description,
                                    about_company=None,
                                    user_information_all=user_information_all,
                                )
                            elif ai_provider.lower() == "openclaw":
                                answer = openclaw_answer_question(
                                    aiClient,
                                    label_org,
                                    question_type="text",
                                    job_description=job_description,
                                    user_information_all=user_information_all,
                                )
                            else:
                                randomly_answered_questions.add((label_org, "text"))
                                answer = years_of_experience
                            if answer and isinstance(answer, str) and len(answer) > 0:
                                print_lg(
                                    f'AI Answered received for question "{label_org}" \nhere is answer: "{answer}"'
                                )
                            else:
                                randomly_answered_questions.add((label_org, "text"))
                                answer = years_of_experience
                        except Exception as e:
                            print_lg("Failed to get AI answer!", e)
                            randomly_answered_questions.add((label_org, "text"))
                            answer = years_of_experience
                    else:
                        randomly_answered_questions.add((label_org, "text"))
                        answer = years_of_experience
                ##<
                text.clear()
                text.send_keys(answer)
                if do_actions:
                    sleep(2)
                    actions.send_keys(Keys.ARROW_DOWN)
                    actions.send_keys(Keys.ENTER).perform()
            questions_list.add(
                (label, text.get_attribute("value"), "text", prev_answer)
            )
            continue

        # Check if it's a textarea question
        text_area = try_xp(Question, ".//textarea", False)
        if text_area:
            label = try_xp(Question, ".//label[@for]", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = ""
            prev_answer = text_area.get_attribute("value")
            if not prev_answer or overwrite_previous_answers:
                if "summary" in label:
                    answer = linkedin_summary
                elif "cover" in label:
                    answer = cover_letter
                if answer == "":
                    ##> ------ Yang Li : MARKYangL - Feature ------
                    if use_AI and aiClient:
                        try:
                            if ai_provider.lower() == "openai":
                                answer = ai_answer_question(
                                    aiClient,
                                    label_org,
                                    question_type="textarea",
                                    job_description=job_description,
                                    user_information_all=user_information_all,
                                )
                            elif ai_provider.lower() == "deepseek":
                                answer = deepseek_answer_question(
                                    aiClient,
                                    label_org,
                                    options=None,
                                    question_type="textarea",
                                    job_description=job_description,
                                    about_company=None,
                                    user_information_all=user_information_all,
                                )
                            elif ai_provider.lower() == "gemini":
                                answer = gemini_answer_question(
                                    aiClient,
                                    label_org,
                                    options=None,
                                    question_type="textarea",
                                    job_description=job_description,
                                    about_company=None,
                                    user_information_all=user_information_all,
                                )
                            elif ai_provider.lower() == "openclaw":
                                answer = openclaw_answer_question(
                                    aiClient,
                                    label_org,
                                    question_type="textarea",
                                    job_description=job_description,
                                    user_information_all=user_information_all,
                                )
                            else:
                                randomly_answered_questions.add((label_org, "textarea"))
                                answer = ""
                            if answer and isinstance(answer, str) and len(answer) > 0:
                                print_lg(
                                    f'AI Answered received for question "{label_org}" \nhere is answer: "{answer}"'
                                )
                            else:
                                randomly_answered_questions.add((label_org, "textarea"))
                                answer = ""
                        except Exception as e:
                            print_lg("Failed to get AI answer!", e)
                            randomly_answered_questions.add((label_org, "textarea"))
                            answer = ""
                    else:
                        randomly_answered_questions.add((label_org, "textarea"))
            text_area.clear()
            text_area.send_keys(answer)
            if do_actions:
                sleep(2)
                actions.send_keys(Keys.ARROW_DOWN)
                actions.send_keys(Keys.ENTER).perform()
            questions_list.add(
                (label, text_area.get_attribute("value"), "textarea", prev_answer)
            )
            ##<
            continue

        # Check if it's a checkbox question
        checkbox = try_xp(Question, ".//input[@type='checkbox']", False)
        if checkbox:
            label = try_xp(Question, ".//span[@class='visually-hidden']", False)
            label_org = label.text if label else "Unknown"
            label = label_org.lower()
            answer = try_xp(
                Question, ".//label[@for]", False
            )  # Sometimes multiple checkboxes are given for 1 question, Not accounted for that yet
            answer = answer.text if answer else "Unknown"
            prev_answer = checkbox.is_selected()
            checked = prev_answer
            if not prev_answer:
                try:
                    actions.move_to_element(checkbox).click().perform()
                    checked = True
                except Exception as e:
                    print_lg("Checkbox click failed!", e)
                    pass
            questions_list.add(
                (f"{label} ([X] {answer})", checked, "checkbox", prev_answer)
            )
            continue

    # Select todays date
    try_xp(driver, "//button[contains(@aria-label, 'This is today')]")

    # Collect important skills
    # if 'do you have' in label and 'experience' in label and ' in ' in label -> Get word (skill) after ' in ' from label
    # if 'how many years of experience do you have in ' in label -> Get word (skill) after ' in '

    return questions_list

