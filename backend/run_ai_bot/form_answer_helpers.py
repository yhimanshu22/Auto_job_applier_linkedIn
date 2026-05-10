"""
Accurate form-filling plan (operational contract for Easy Apply):

1. **Single source of truth** — `years_of_experience` in personals/config is the canonical
   **total professional** years answer unless the question is clearly **skill-scoped**.

2. **Label classification**
   - **Total YOE** → always use `years_of_experience` for text/textarea when the label matches
     `should_fill_total_years_from_config()` (expanded keywords, exclusions for age/DOB).
   - **Skill-scoped** (e.g. "years with Python") → do **not** force total years; use AI / custom_qa.
   - **Experience dropdowns** → map configured years to the closest **bucket option** via
     `select_bucket_for_total_years()` instead of random `select_by_index`.

3. **AI fallback** — When AI is used, append **canonical years** to the prompt so total-YOE
   questions cannot drift (10 vs 22) due to resume inference.

4. **Custom overrides** — `config/custom_qa.json` remains the override for awkward labels.

5. **Ongoing** — Periodically review `randomly_answered_questions` logs and add custom_qa entries.
"""

from __future__ import annotations

import re
from typing import Iterable


def _parse_years_int(years_str: str | None) -> int | None:
    if not years_str:
        return None
    m = re.search(r"(\d+)", str(years_str))
    return int(m.group(1)) if m else None


def _excluded_age_or_irrelevant(label_lower: str) -> bool:
    if "year" not in label_lower and "years" not in label_lower:
        return False
    bad = (
        "years of age",
        "under 18",
        "over 18",
        "age 18",
        "how old",
        "date of birth",
        "date-of-birth",
        "dob",
        "birth",
        "parental",
        "maternity",
        "paternity",
    )
    return any(b in label_lower for b in bad)


def is_skill_scoped_experience_question(label_lower: str) -> bool:
    """
    True when the question asks for years/experience in ONE skill/tool, not total career.
    """
    if re.search(r"\b(years?|yoe)\b.{0,48}\b(in|with)\b", label_lower):
        generic = (
            "software development",
            "software engineering",
            "this role",
            "this position",
            "your field",
            "the industry",
            "development",
            "engineering role",
        )
        if any(g in label_lower for g in generic):
            return False
        return True
    if re.search(r"\bexperience\s+(in|with)\s+[a-z0-9]", label_lower):
        if any(
            g in label_lower
            for g in (
                "professional experience",
                "work experience",
                "relevant experience",
                "overall experience",
            )
        ):
            return False
        return True
    return False


def should_fill_total_years_from_config(label_org: str) -> bool:
    """
    Use configured `years_of_experience` for this field (text or bucket selection).
    Narrower than the old `experience in label or years in label` rule.
    """
    l = label_org.lower().strip()
    if _excluded_age_or_irrelevant(l):
        return False
    if is_skill_scoped_experience_question(l):
        return False
    if "yoe" in l:
        return True
    if "total years" in l or "overall years" in l:
        return True
    if any(
        x in l
        for x in (
            "years of professional",
            "years of work",
            "years of relevant",
            "years of industry",
        )
    ):
        return True
    if "career" in l and ("year" in l or "length" in l):
        return True
    if "tenure" in l:
        return True
    if "how many years" in l and any(
        x in l for x in ("experience", "professional", "work", "career", "industry", "relevant")
    ):
        return True
    if "experience" in l and any(x in l for x in ("year", "years", "yrs")):
        return True
    if "years" in l or "yrs" in l:
        return any(
            x in l
            for x in (
                "professional",
                "work",
                "career",
                "industry",
                "total",
                "relevant",
                "software",
                "engineering",
                "developer",
                "full stack",
                "full-stack",
            )
        )
    return False


def is_experience_level_select(label_org: str) -> bool:
    """Dropdown likely listing year ranges or seniority tied to YOE."""
    l = label_org.lower()
    if _excluded_age_or_irrelevant(l):
        return False
    keys = (
        "experience",
        "yoe",
        "years",
        "tenure",
        "seniority",
        "career",
        "professional background",
    )
    return any(k in l for k in keys)


def select_bucket_for_total_years(
    years_str: str, options: Iterable[str]
) -> str | None:
    """
    Pick the select option whose numeric range best matches configured total years.
    Returns None if no option could be scored.
    """
    y = _parse_years_int(years_str)
    if y is None:
        return None
    opts = [
        o.strip()
        for o in options
        if o and o.strip() and "select an option" not in o.lower()
    ]
    if not opts:
        return None

    best_opt: str | None = None
    best_score: float = 1e18

    for opt in opts:
        ol = opt.lower()
        nums = [int(x) for x in re.findall(r"\d+", opt)]
        score: float
        if len(nums) >= 2:
            lo, hi = min(nums[0], nums[1]), max(nums[0], nums[1])
            if lo <= y <= hi:
                score = 0.0
            elif y < lo:
                score = float(lo - y) + 0.5
            else:
                score = float(y - hi) + 0.5
        elif len(nums) == 1:
            n = nums[0]
            if "+" in opt or "plus" in ol or "or more" in ol or "more than" in ol:
                score = 0.0 if y >= n else float(n - y) + 2.0
            elif "under" in ol or "less than" in ol or "up to" in ol:
                score = 0.0 if y <= n else float(y - n) + 2.0
            else:
                score = abs(float(y - n))
        else:
            continue

        if score < best_score:
            best_score = score
            best_opt = opt

    return best_opt
