"""Scan the LinkedIn feed for job / intern posts with apply instructions."""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from selenium.webdriver.common.by import By

from .. import config
from .engage_dom import EngageDomMixin
from .engage_utils import pause_between

# Signals that a post may contain a hiring / intern opportunity.
_DEFAULT_KEYWORDS: tuple[str, ...] = (
    "intern",
    "internship",
    "hiring",
    "job opening",
    "job opportunity",
    "we're hiring",
    "we are hiring",
    "apply now",
    "apply here",
    "send your resume",
    "send your cv",
    "send resume",
    "drop your resume",
    "fill the form",
    "fill out the form",
    "application form",
    "campus hiring",
    "campus recruitment",
    "open role",
    "open position",
    "looking to hire",
    "looking for intern",
    "looking for candidates",
    "recruiting",
)

# Too broad alone — only count with another hiring signal or a contact link.
_WEAK_KEYWORDS: tuple[str, ...] = (
    "looking for",
)

# LinkedIn feed chrome that pollutes ``post.text`` in the 2026 UI.
_FEED_NOISE_LINE_RE = re.compile(
    r"^(feed post|.+ (likes|like|supports|support) this|\d+(st|nd|rd|th)|"
    r".+ and .+ (like|likes) this)$",
    re.IGNORECASE,
)

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)

# Skip generic LinkedIn / social links when collecting apply URLs.
_URL_SKIP_FRAGMENTS = (
    "linkedin.com/feed",
    "linkedin.com/in/",
    "linkedin.com/company/",
    "linkedin.com/posts/",
    "linkedin.com/safety/go/",
    "linkedin.com/search/results/",
    "linkedin.com/job-posting/",
    "licdn.com",
    "lnkd.in",
    "facebook.com",
    "twitter.com",
    "instagram.com",
)

# Prefer these when present (forms, ATS, careers pages).
_URL_PRIORITY_FRAGMENTS = (
    "forms.gle",
    "docs.google.com/forms",
    "typeform.com",
    "tally.so",
    "notion.site",
    "notion.so",
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "workday.com",
    "careers.",
    "jobs.",
    "apply",
    "application",
)


class OpportunityScanMixin(EngageDomMixin):
    """Scroll the home feed and collect job / intern opportunities from posts."""

    def scan_feed_opportunities(
        self,
        max_posts: int = 50,
        keywords: Optional[List[str]] = None,
        output_file: str = "opportunities.json",
        post_extractor=None,
        require_contact: bool = False,
    ) -> Dict[str, Any]:
        """Scan feed posts for hiring/intern content and extract apply details.

        By default, posts that match hiring keywords are saved even when no
        email or apply URL is found (``has_contact=false`` on the entry).
        Pass ``require_contact=True`` to keep only posts with emails or URLs.
        """
        results: Dict[str, Any] = {
            "posts_scanned": 0,
            "found": 0,
            "opportunities": [],
            "output_file": output_file,
            "errors": [],
            "success": False,
        }
        if max_posts <= 0:
            return results

        kw_list = [k.strip().lower() for k in (keywords or []) if k and str(k).strip()]
        if not kw_list:
            kw_list = list(_DEFAULT_KEYWORDS)

        try:
            self._navigate_opportunity_feed()
        except Exception as exc:
            results["errors"].append(f"Could not open feed: {exc}")
            return results

        seen_keys: Set[str] = set()
        opportunities: List[Dict[str, Any]] = []
        stalled = 0
        stall_budget = 10
        started_at = datetime.now(timezone.utc).isoformat()

        self._persist_opportunities(
            output_file,
            opportunities,
            posts_scanned=0,
            started_at=started_at,
            in_progress=True,
        )

        while results["posts_scanned"] < max_posts and stalled < stall_budget:
            posts = self._find_visible_posts(limit=12)
            if not posts:
                self._scroll_feed(1.2, 2.4)
                stalled += 1
                continue

            progress = False
            for post in posts:
                if results["posts_scanned"] >= max_posts:
                    break
                try:
                    urn = self._extract_post_urn(post)
                    key = self._post_dedupe_key(post, urn)
                except Exception:
                    key = str(id(post))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                results["posts_scanned"] += 1
                progress = True

                text = self._read_post_text(post, post_extractor)
                clean_text = self._clean_opportunity_text(text)
                emails = self._extract_emails(clean_text)
                urls = self._extract_apply_urls(clean_text, post)
                has_job_link = any("/jobs/view/" in u for u in urls)

                if not (has_job_link or self._looks_like_opportunity(clean_text, kw_list)):
                    continue
                if require_contact and not emails and not urls:
                    logging.info(
                        "OPPORTUNITY skip no_contact key=%s snippet=%r",
                        key[:40],
                        clean_text[:80],
                    )
                    continue

                has_contact = bool(emails or urls)
                author = self._extract_author_name(post) or ""
                post_url = self._extract_post_permalink(post, urn)
                snippet = " ".join(clean_text.split())[:280]
                matched = [kw for kw in kw_list if kw in clean_text.lower()]
                if has_job_link and "linkedin job" not in matched:
                    matched.append("linkedin job")

                entry = {
                    "author": author,
                    "post_urn": urn,
                    "post_url": post_url,
                    "snippet": snippet,
                    "emails": emails,
                    "urls": urls,
                    "has_contact": has_contact,
                    "keywords_matched": matched,
                    "found_at": datetime.now(timezone.utc).isoformat(),
                }
                opportunities.append(entry)
                results["found"] = len(opportunities)
                logging.info(
                    "OPPORTUNITY found author=%r contact=%s emails=%s urls=%s",
                    author,
                    has_contact,
                    emails,
                    urls,
                )
                try:
                    self._persist_opportunities(
                        output_file,
                        opportunities,
                        posts_scanned=results["posts_scanned"],
                        started_at=started_at,
                        in_progress=True,
                    )
                except OSError as exc:
                    results["errors"].append(
                        f"Could not write {output_file}: {exc}"
                    )

            if results["posts_scanned"] >= max_posts:
                break
            if progress:
                stalled = 0
            else:
                stalled += 1
                if stalled >= 2:
                    if self._aggressive_load_more(list(seen_keys), tries=3):
                        stalled = 0
            self._scroll_feed(1.2, 2.4)

        results["opportunities"] = opportunities
        results["found"] = len(opportunities)
        results["success"] = True

        try:
            self._persist_opportunities(
                output_file,
                opportunities,
                posts_scanned=results["posts_scanned"],
                started_at=started_at,
                in_progress=False,
            )
            logging.info(
                "OPPORTUNITY saved count=%d file=%s", results["found"], output_file
            )
        except OSError as exc:
            results["errors"].append(f"Could not write {output_file}: {exc}")

        logging.info(
            "OPPORTUNITY summary scanned=%s found=%s",
            results["posts_scanned"],
            results["found"],
        )
        return results

    def _persist_opportunities(
        self,
        output_file: str,
        opportunities: List[Dict[str, Any]],
        *,
        posts_scanned: int,
        started_at: str,
        in_progress: bool,
    ) -> None:
        """Write the current scan snapshot to disk (called after each find)."""
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "started_at": started_at,
            "updated_at": now,
            "scanned_at": now,
            "posts_scanned": posts_scanned,
            "found": len(opportunities),
            "in_progress": in_progress,
            "opportunities": opportunities,
        }
        with open(output_file, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        if opportunities:
            logging.info(
                "OPPORTUNITY flushed count=%d scanned=%d file=%s",
                len(opportunities),
                posts_scanned,
                output_file,
            )

    def _navigate_opportunity_feed(self) -> None:
        try:
            self.driver.get(config.LINKEDIN_FEED_URL)
        except Exception:
            pass
        pause_between(config.MIN_PAGE_LOAD_DELAY, config.MAX_PAGE_LOAD_DELAY)
        try:
            self.dismiss_overlays()
        except Exception:
            pass

    def _read_post_text(self, post, post_extractor) -> str:
        if post_extractor and hasattr(post_extractor, "extract_text"):
            try:
                text = (post_extractor.extract_text(post) or "").strip()
                if text:
                    return text
            except Exception:
                pass
        try:
            parts: List[str] = []
            seen: set[str] = set()
            for xp in (
                ".//div[contains(@class,'update-components-text')]//*[normalize-space()]",
                ".//div[contains(@class,'feed-shared-inline-show-more-text')]//*[normalize-space()]",
                ".//span[contains(@class,'break-words') and normalize-space()]",
                ".//div[@dir]//span[normalize-space() and string-length(normalize-space(.))>25]",
            ):
                try:
                    for node in post.find_elements(By.XPATH, xp):
                        snippet = (node.text or "").strip()
                        if snippet and snippet not in seen:
                            seen.add(snippet)
                            parts.append(snippet)
                    if parts:
                        break
                except Exception:
                    continue
            if parts:
                return "\n".join(parts)
            return (post.text or "").strip()
        except Exception:
            return ""

    def _clean_opportunity_text(self, text: str) -> str:
        if not text:
            return ""
        lines = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line or _FEED_NOISE_LINE_RE.match(line):
                continue
            lines.append(line)
        return "\n".join(lines).strip()

    def _looks_like_opportunity(self, text: str, keywords: List[str]) -> bool:
        if not text:
            return False
        lower = text.lower()
        if any(kw in lower for kw in keywords):
            return True
        if any(kw in lower for kw in _WEAK_KEYWORDS):
            return any(
                signal in lower
                for signal in (
                    "intern",
                    "internship",
                    "hiring",
                    "recruit",
                    "apply",
                    "resume",
                    "cv",
                    "opening",
                    "role",
                    "position",
                    "campus",
                )
            )
        return False

    def _extract_emails(self, text: str) -> List[str]:
        seen: set[str] = set()
        out: List[str] = []
        for match in _EMAIL_RE.findall(text or ""):
            email = match.strip().rstrip(".,;:")
            key = email.lower()
            if key not in seen:
                seen.add(key)
                out.append(email)
        return out

    def _extract_apply_urls(self, text: str, post) -> List[str]:
        seen: set[str] = set()
        candidates: List[str] = []

        for match in _URL_RE.findall(text or ""):
            url = match.strip().rstrip(".,;)")
            if any(skip in url.lower() for skip in _URL_SKIP_FRAGMENTS):
                continue
            if url not in seen:
                seen.add(url)
                candidates.append(url)

        # Embedded job cards, apply buttons, and forms often omit URLs from innerText.
        link_xpaths = (
            ".//a[contains(@href,'/jobs/view/')]",
            ".//a[contains(@href,'/jobs/collections/')]",
            ".//a[contains(@href,'forms.gle')]",
            ".//a[contains(@href,'docs.google.com/forms')]",
            ".//a[contains(@href,'typeform.com')]",
            ".//a[contains(@href,'greenhouse.io')]",
            ".//a[contains(@href,'lever.co')]",
            ".//a[starts-with(@href,'http')]",
        )
        for xp in link_xpaths:
            try:
                for el in post.find_elements(By.XPATH, xp):
                    href = (el.get_attribute("href") or "").split("?")[0]
                    if not href or any(skip in href.lower() for skip in _URL_SKIP_FRAGMENTS):
                        continue
                    if href not in seen:
                        seen.add(href)
                        candidates.append(href)
            except Exception:
                continue

        def _rank(url: str) -> tuple[int, str]:
            lower = url.lower()
            priority = 0
            if any(p in lower for p in _URL_PRIORITY_FRAGMENTS):
                priority = 1
            return (-priority, url)

        candidates.sort(key=_rank)
        return candidates[:10]

    def _extract_post_permalink(self, post, urn: Optional[str]) -> Optional[str]:
        try:
            for el in post.find_elements(
                By.XPATH,
                ".//a[contains(@href,'/feed/update/') or contains(@href,'/posts/')]",
            ):
                href = el.get_attribute("href")
                if href:
                    return href.split("?")[0]
        except Exception:
            pass
        if urn and "activity:" in str(urn):
            activity_id = str(urn).split("activity:")[-1].split(",")[0].strip()
            if activity_id:
                return f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}/"
        return None
