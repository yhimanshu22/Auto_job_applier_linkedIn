"""Parse and format dashboard pseudo-Python config files."""

from __future__ import annotations

import ast
import json
import re

# Keys that must be lists for the job-applier validator (search category).
SEARCH_LIST_KEYS = frozenset(
    {
        "search_terms",
        "experience_level",
        "job_type",
        "on_site",
        "companies",
        "location",
        "industry",
        "job_function",
        "job_titles",
        "benefits",
        "commitments",
        "about_company_bad_words",
        "about_company_good_words",
        "bad_words",
    }
)


def _try_literal_list(value: str):
    text = value.strip()
    if not text.startswith("["):
        return None
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return None
    return parsed if isinstance(parsed, list) else None


def normalize_stored_value(key: str, value):
    """Repair corrupted DB values (e.g. literal ``'['``) before export to the UI."""
    if value is None:
        return [] if key in SEARCH_LIST_KEYS else ""
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return value

    text = value.strip()
    if key in SEARCH_LIST_KEYS:
        if text in ("[", '["', "']", '"[]"'):
            return []
        as_list = _try_literal_list(text)
        if as_list is not None:
            return as_list
        if text:
            return [text]
        return []
    return value


def parse_config_value(value_str: str, key: str = ""):
    """Parse one RHS from ``key = value`` in a config file."""
    value_str = value_str.strip()
    if not value_str:
        return ""

    if (value_str.startswith('"') and value_str.endswith('"')) or (
        value_str.startswith("'") and value_str.endswith("'")
    ):
        inner = value_str[1:-1]
        inner = inner.replace("\\n", "\n").replace('\\"', '"')
        if key in SEARCH_LIST_KEYS or inner.strip().startswith("["):
            as_list = _try_literal_list(inner)
            if as_list is not None:
                return as_list
        if key in SEARCH_LIST_KEYS and inner.strip() in ("[", ""):
            return []
        return inner

    lowered = value_str.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    as_list = _try_literal_list(value_str)
    if as_list is not None:
        return as_list

    if value_str in ("[", '["'):
        return []

    if re.fullmatch(r"-?\d+", value_str):
        return int(value_str)
    try:
        return float(value_str)
    except ValueError:
        pass

    if key in SEARCH_LIST_KEYS:
        return [] if not value_str else [value_str]
    return value_str


def format_config_value(value) -> str:
    """Serialize a Python value for pseudo-config file content."""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, list):
        return json.dumps(value).replace('"', "'")
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    if value is None:
        return '""'
    return str(value)


def parse_config_content(content: str) -> dict:
    """Parse a full config file into a dict (supports multi-line quoted strings)."""
    parsed: dict = {}
    lines = content.split("\n")
    current_key = ""
    current_value = ""
    in_quoted_string = False
    quote_char = '"'

    for line in lines:
        if not in_quoted_string:
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            current_key = key.strip()
            val = val.strip()

            if val.startswith('"') or val.startswith("'"):
                quote_char = val[0]
                in_quoted_string = True
                current_value = val[1:]
                if current_value.endswith(quote_char) and len(current_value) > 0:
                    in_quoted_string = False
                    parsed[current_key] = parse_config_value(
                        quote_char + current_value[:-1] + quote_char, current_key
                    )
            else:
                parsed[current_key] = parse_config_value(val, current_key)
        else:
            if line.endswith(quote_char):
                in_quoted_string = False
                current_value += "\n" + line[: -len(quote_char)]
                parsed[current_key] = parse_config_value(
                    quote_char + current_value + quote_char, current_key
                )
            else:
                current_value += "\n" + line

    if in_quoted_string and current_key:
        parsed[current_key] = parse_config_value(
            quote_char + current_value + quote_char, current_key
        )

    return parsed


def format_config_content(category: str, config_data: dict) -> str:
    header = f"################ {category.upper()} CONFIGURATION ################\n\n"
    lines = [header]
    for key, value in config_data.items():
        if category == "search":
            value = normalize_stored_value(key, value)
        lines.append(f"{key} = {format_config_value(value)}\n")
    return "".join(lines)
