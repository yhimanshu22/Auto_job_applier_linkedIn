
from config.config_bridge import *

import re
import time

from modules.helpers import print_lg, critical_error_log, convert_to_json
from modules.ai.prompts import *

from pyautogui import confirm
from openai import OpenAI
from openai.types.model import Model
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from typing import Iterator, Literal


def _is_rate_limit_error(e: BaseException) -> bool:
    """Groq/OpenAI-compatible providers often return 429 or embed details in the message body."""
    code = getattr(e, "status_code", None)
    if code == 429:
        return True
    if type(e).__name__ == "RateLimitError":
        return True
    s = str(e).lower()
    return (
        "429" in s
        or "rate limit" in s
        or "rate_limit" in s
        or "too many requests" in s
    )


def _parse_retry_after_seconds(exc: BaseException) -> float | None:
    """Parse delays like Groq: 'Please try again in 16m47.424s'."""
    text = str(exc)
    m = re.search(r"try again in (\d+)m([\d.]+)s", text, re.I)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    m = re.search(r"try again in ([\d.]+)s", text, re.I)
    if m:
        return float(m.group(1))
    return None


def _normalize_llm_json_text(raw: str) -> str:
    """Strip ```json ... ``` fences so json.loads / convert_to_json can succeed."""
    if not raw:
        return raw
    s = raw.strip()
    if not s.startswith("```"):
        return s
    lines = s.splitlines()
    if len(lines) < 2:
        return s
    lines = lines[1:]
    while lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


apiCheckInstructions = """

1. Make sure your OpenClaw API connection details like url, model names, etc are correct.
2. Ensure the OpenClaw server is running.

Open `secret.py` in `/config` folder to configure your AI API connections.

ERROR:
"""

# Function to show an AI error alert
def ai_error_alert(message: str, stackTrace: str, title: str = "OpenClaw Connection Error") -> None:
    """
    Function to show an AI error alert and log it.
    """
    global showAiErrorAlerts
    if showAiErrorAlerts:
        if "Pause AI error alerts" == confirm(f"{message}{stackTrace}\n", title, ["Pause AI error alerts", "Okay Continue"]):
            showAiErrorAlerts = False
    critical_error_log(message, stackTrace)


# Function to check if an error occurred
def ai_check_error(response: ChatCompletion | ChatCompletionChunk) -> None:
    """
    Function to check if an error occurred.
    * Takes in `response` of type `ChatCompletion` or `ChatCompletionChunk`
    * Raises a `ValueError` if an error is found
    """
    if response.model_extra and response.model_extra.get("error"):
        raise ValueError(
            f'Error occurred with API: "{response.model_extra.get("error")}"'
        )


# Function to create an OpenAI client tailored for OpenClaw
def ai_create_openai_client() -> OpenAI:
    """
    Function to create an OpenClaw compatible client via the official OpenAI library.
    * Returns an `OpenAI` object
    """
    try:
        print_lg("Creating OpenClaw compatible client...")
        if not use_AI:
            raise ValueError("AI is not enabled! Please enable it by setting `use_AI = True` in `secrets.py` in `config` folder.")
        
        # When using OpenClaw with local models, an API key might be empty or 'not-needed'.
        # The openai library enforces the presence of an api_key string.
        # So we default to 'openclaw-dummy-key' if it's missing or effectively null.
        effective_api_key = llm_api_key.strip() if llm_api_key else ""
        if not effective_api_key or effective_api_key.lower() == "not-needed":
             effective_api_key = "openclaw-dummy-key"

        client = OpenAI(base_url=llm_api_url, api_key=effective_api_key)

        print_lg("---- SUCCESSFULLY CREATED OPENCLAW CLIENT! ----")
        print_lg(f"Using API URL: {llm_api_url}")
        print_lg(f"Using Model: {llm_model}")
        print_lg("Check './config/secrets.py' for more details.\n")
        print_lg("---------------------------------------------")

        return client
    except Exception as e:
        ai_error_alert(f"Error occurred while creating OpenClaw client. {apiCheckInstructions}", e)


# Function to close an OpenAI client
def ai_close_openai_client(client: OpenAI) -> None:
    """
    Function to close an OpenClaw compatible client.
    * Takes in `client` of type `OpenAI`
    * Returns no value
    """
    try:
        if client:
            print_lg("Closing OpenClaw client...")
            client.close()
    except Exception as e:
        ai_error_alert("Error occurred while closing OpenClaw client.", e)


# Function to get chat completion from OpenAI API
def ai_completion(client: OpenAI, messages: list[dict], response_format: dict = None, temperature: float = 0, stream: bool = stream_output) -> dict | ValueError:
    """
    Function that completes a chat and prints and formats the results.
    * Takes in `client` of type `OpenAI`
    * Takes in `messages` of type `list[dict]`
    * Returns a `dict` object representing JSON response
    """
    if not client:
        raise ValueError("Client is not available!")

    # One retry on 429: short wait (cap so we don't block the bot for Groq's multi-minute TPD windows).
    max_rounds = 2
    completion = None
    current_stream = stream
    for round_i in range(max_rounds):
        params = {"model": llm_model, "messages": messages, "stream": current_stream}
        if response_format:
            params["response_format"] = response_format
        try:
            completion = client.chat.completions.create(**params)
            break
        except Exception as e:
            if _is_rate_limit_error(e) and round_i + 1 < max_rounds:
                delay = _parse_retry_after_seconds(e)
                if delay is None:
                    delay = 45.0
                delay = min(delay, 90.0)
                print_lg(
                    f"OpenClaw/Groq rate limited (429). Waiting {delay:.0f}s, then one retry (non-stream). "
                    f"[{round_i + 1}/{max_rounds}]"
                )
                time.sleep(delay)
                current_stream = False
                continue
            raise

    result = ""

    # Log response
    if current_stream:
        print_lg("--STREAMING STARTED")
        for chunk in completion:
            ai_check_error(chunk)
            chunkMessage = chunk.choices[0].delta.content
            if chunkMessage != None:
                result += chunkMessage
            print_lg(chunkMessage, end="", flush=True)
        print_lg("\n--STREAMING COMPLETE")
    else:
        ai_check_error(completion)
        if len(completion.choices) > 0 and completion.choices[0].message and completion.choices[0].message.content:
            result = completion.choices[0].message.content

    if response_format:
        result = convert_to_json(result)

    print_lg("\nAI Answer to Question:\n")
    print_lg(result, pretty=response_format is not None)
    return result


def ai_extract_skills(client: OpenAI, job_description: str, stream: bool = stream_output) -> dict | ValueError:
    """
    Function to extract skills from job description using OpenClaw compatible API.
    * Returns a `dict` object representing JSON response
    """
    print_lg("-- EXTRACTING SKILLS FROM JOB DESCRIPTION (via OpenClaw)")
    try:
        # Groq and many OpenAI-compatible hosts do not support response_format json_schema.
        # Use prompt-only JSON + parse (same idea as DeepSeek path).
        prompt = extract_skills_prompt.format(job_description)
        prompt += (
            "\n\nRespond with ONLY a single valid JSON object matching the schema above. "
            "No markdown fences, no commentary."
        )
        messages = [{"role": "user", "content": prompt}]
        raw = ai_completion(client, messages, response_format=None, stream=stream)
        if not isinstance(raw, str):
            return raw
        raw = _normalize_llm_json_text(raw)
        return convert_to_json(raw)
    except Exception as e:
        if _is_rate_limit_error(e):
            print_lg(
                "Groq/OpenClaw rate limit — skipping AI skill extraction for this job (same as when AI is unavailable). "
                "Upgrade quota or switch model in secrets when daily tokens are exhausted."
            )
            critical_error_log("OpenClaw rate limit during skill extraction", e)
            return None
        ai_error_alert(
            f"Error occurred while extracting skills from job description. {apiCheckInstructions}", e
        )


def ai_answer_question(
    client: OpenAI, 
    question: str, options: list[str] | None = None, question_type: Literal['text', 'textarea', 'single_select', 'multiple_select'] = 'text', 
    job_description: str = None, about_company: str = None, user_information_all: str = None,
    stream: bool = stream_output
) -> dict | ValueError:
    """
    Function to generate AI-based answers for questions in a form via OpenClaw.
    """

    print_lg("-- ANSWERING QUESTION using OpenClaw AI")
    try:
        prompt = ai_answer_prompt.format(user_information_all or "N/A", question)
        prompt += canonical_experience_instruction()
         # Append optional details if provided
        if job_description and job_description != "Unknown":
            prompt += f"\nJob Description:\n{job_description}"
        if about_company and about_company != "Unknown":
            prompt += f"\nAbout the Company:\n{about_company}"

        messages = [{"role": "user", "content": prompt}]
        print_lg("Prompt we are passing to AI: ", prompt)
        response = ai_completion(client, messages, stream=stream)
        return response
    except Exception as e:
        if _is_rate_limit_error(e):
            print_lg(
                "Groq/OpenClaw rate limit — skipping AI for this question; runAiBot will use rule/default answers."
            )
            critical_error_log("OpenClaw rate limit during question answer", e)
            return ""
        ai_error_alert(f"Error occurred while answering question. {apiCheckInstructions}", e)
