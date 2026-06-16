"""
Profile interaction methods for LinkedIn automation.

Why:
    Encapsulates all profile-related actions like searching, following, and
    interacting with a profile's posts in a single module.

When:
    Used when the bot needs to engage with specific profiles programmatically,
    such as in the "Operation Pursue the Investor" feature.

How:
    Provides methods to search for profiles, follow/unfollow, and interact with
    a profile's posts, using Selenium WebDriver for browser automation.
"""

import logging
import os
import random
import re
import time
import urllib.parse
from typing import List, Optional, Callable, Any, Dict, Set
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Where diagnostic dumps go. Mirrors what engage_flow uses so all
# debugging artifacts land in one place.
_DIAG_DIR = os.path.join("logs", "diag")


# Selector inventory for people-search results. LinkedIn ships A/B layouts
# fairly often; the search code walks this list and stops at the first
# selector that yields any matches.
_RESULT_SELECTORS = [
    # LinkedIn 2026+ people search — obfuscated classes, componentkey per result.
    "//div[starts-with(@componentkey,'SearchResultsACo')]",
    "//div[contains(@componentkey,'SearchResults') and .//a[contains(@href,'/in/')]]",
    # Modern (universal template) — most common as of 2024-2026.
    "//div[contains(@class,'entity-result')]",
    "//div[@data-chameleon-result-urn]",
    "//li[contains(@class,'reusable-search__result-container')]",
    "//li[.//div[@data-chameleon-result-urn]]",
    "//li[.//span[contains(@class,'entity-result__title')]]",
    # Universal search template (recently rolled out in some accounts).
    "//div[@data-view-name='search-entity-result-universal-template']",
    # Fallback — any container that has an /in/ link in it.
    "//li[.//a[contains(@href,'/in/')]]",
]


# Selectors for the global-nav typeahead input. LinkedIn flips between
# input[role='combobox'] and a plain text input wrapped in a labelled span.
_TYPEAHEAD_SELECTORS = [
    "input[role='combobox']",
    "input.search-global-typeahead__input",
    "input[placeholder*='Search']",
    "input[aria-label*='Search']",
    "#global-nav-typeahead input",
]

# LinkedIn invite modal — "Send without a note" is an artdeco primary button.
_SEND_WITHOUT_NOTE_XPATHS = (
    "//span[contains(@class,'artdeco-button__text') and normalize-space()='Send without a note']",
    "//span[contains(@class,'artdeco-button__text') and contains(normalize-space(.), 'Send without a note')]/ancestor::button[1]",
    "//button[.//span[contains(@class,'artdeco-button__text') and contains(., 'Send without a note')]]",
    "//body/div[1]/div[4]//span[contains(@class,'artdeco-button__text') and contains(., 'Send without a note')]/ancestor::button[1]",
    "/html/body/div[1]/div[4]//div/div[1]/div/div/div[3]/button[2]",
    "//body/div[1]/div[4]//div/div[1]/div/div/div[3]/button[2]",
    "//body/div[1]/div[4]//button[contains(., 'Send without a note')]",
)


class ProfileActionsMixin:
    """Mixin class for profile-related interactions on LinkedIn."""

    def search_profile(
        self, name: str, bio_keywords: List[str] = None
    ) -> Optional[str]:
        """Search for a profile and return its URL if found.

        Strategy (in order):
          1. Navigate directly to the people-search results URL — bypasses
             the typeahead entirely so we're immune to LinkedIn flipping the
             search box CSS / ARIA, and skips the "click People tab" step
             because the URL is scoped to people already.
          2. If the results page renders no matches (rare), fall back to
             the legacy typeahead-then-Enter flow.

        On total failure a single HTML + PNG snapshot is dumped under
        ``logs/diag/pursue_<reason>_<ts>.{html,png}`` so we can tell apart
        empty results from a checkpoint / captcha / DOM change.
        """
        if not name or not str(name).strip():
            return None
        name = str(name).strip()

        try:
            logging.info("PURSUE_SEARCH start name=%r", name)
            url_result = self._search_profile_via_url(name, bio_keywords)
            if url_result:
                return url_result

            logging.info(
                "PURSUE_SEARCH url_strategy_returned_no_results — trying typeahead"
            )
            ta_result = self._search_profile_via_typeahead(name, bio_keywords)
            if ta_result:
                return ta_result

            self._dump_pursue_diagnostics(reason="no_results", query=name)
            return None
        except Exception as exc:
            logging.error(f"Error in search_profile: {exc}", exc_info=True)
            self._dump_pursue_diagnostics(reason="exception", query=name)
            return None

    # ------------------------------------------------------------------
    # Search strategies
    # ------------------------------------------------------------------

    def _search_profile_via_url(
        self, name: str, bio_keywords: Optional[List[str]]
    ) -> Optional[str]:
        """Deep-link into ``/search/results/people/?keywords=…``.

        This is the most reliable path because:
          - It skips the global-nav typeahead (a frequently-changing widget).
          - It lands us on the People tab — no extra click needed.
          - It supports query parameters LinkedIn officially exposes.
        """
        encoded = urllib.parse.quote_plus(name)
        search_url = (
            "https://www.linkedin.com/search/results/people/"
            f"?keywords={encoded}&origin=GLOBAL_SEARCH_HEADER"
        )
        try:
            self.driver.get(search_url)
        except Exception as exc:
            logging.warning("PURSUE_SEARCH url_navigation_failed: %s", exc)
            return None

        # Wait for the people-results container to render. We don't use a
        # specific selector here because the wrapper class drifts; instead
        # we wait until at least one ``/in/`` anchor shows up anywhere on
        # the page (or the timeout elapses).
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a[href*='/in/']")
                )
            )
        except Exception:
            logging.info("PURSUE_SEARCH url_results_did_not_render_in_15s")
            return None

        # Small settle so React finishes painting the result list.
        time.sleep(1.5)

        return self._pick_profile_from_results(bio_keywords)

    def _search_profile_via_typeahead(
        self, name: str, bio_keywords: Optional[List[str]]
    ) -> Optional[str]:
        """Legacy path: type into the global-nav search and press Enter."""
        try:
            # Make sure we're on a LinkedIn page that *has* the global nav.
            current = (self.driver.current_url or "").lower()
            if "linkedin.com" not in current:
                self.driver.get("https://www.linkedin.com/feed/")
                time.sleep(2.0)
        except Exception:
            pass

        search_box = None
        for sel in _TYPEAHEAD_SELECTORS:
            try:
                search_box = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                if search_box:
                    logging.info("PURSUE_SEARCH typeahead_selector=%s", sel)
                    break
            except Exception:
                continue

        if not search_box:
            logging.warning("PURSUE_SEARCH no_typeahead_found")
            return None

        try:
            search_box.clear()
            search_box.send_keys(name)
            search_box.send_keys(Keys.RETURN)
        except Exception as exc:
            logging.warning("PURSUE_SEARCH typeahead_send_failed: %s", exc)
            return None

        time.sleep(3)

        # Click People tab if available (some search result pages default to
        # All; on others the URL deeplinks straight to People).
        try:
            people_tab = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[.//span[text()='People'] or contains(., 'People')]",
                    )
                )
            )
            people_tab.click()
            time.sleep(2)
        except Exception:
            # Already on people or no tab — fine.
            pass

        return self._pick_profile_from_results(bio_keywords)

    # ------------------------------------------------------------------
    # Result picking
    # ------------------------------------------------------------------

    def _pick_profile_from_results(
        self, bio_keywords: Optional[List[str]]
    ) -> Optional[str]:
        """Walk known result-container selectors; return best-match /in/ URL.

        When ``bio_keywords`` is set we score each result by keyword overlap
        in its visible text. Otherwise we return the first ``/in/`` URL we
        see.
        """
        profile_elements: List = []
        for selector in _RESULT_SELECTORS:
            try:
                els = self.driver.find_elements(By.XPATH, selector)
                if els:
                    profile_elements = els
                    logging.info(
                        "PURSUE_SEARCH selector=%s matches=%d",
                        selector,
                        len(els),
                    )
                    break
            except Exception:
                continue

        if not profile_elements:
            # Last resort: just grab the page's /in/ anchors — useful when
            # LinkedIn restructures the result containers but keeps anchors.
            try:
                anchors = self.driver.find_elements(
                    By.CSS_SELECTOR, "a[href*='/in/']"
                )
                if anchors:
                    href = anchors[0].get_attribute("href")
                    logging.info(
                        "PURSUE_SEARCH used_global_in_anchors first=%s",
                        href,
                    )
                    return href
            except Exception:
                pass
            return None

        if not bio_keywords:
            for el in profile_elements:
                try:
                    link = el.find_element(
                        By.XPATH, ".//a[contains(@href,'/in/')]"
                    )
                    href = link.get_attribute("href")
                    if href:
                        return href
                except Exception:
                    continue
            return None

        normalized = [kw.lower() for kw in bio_keywords if kw]
        for idx, el in enumerate(profile_elements, 1):
            try:
                text = (el.text or "").lower()
                if any(kw in text for kw in normalized):
                    link = el.find_element(
                        By.XPATH, ".//a[contains(@href,'/in/')]"
                    )
                    href = link.get_attribute("href")
                    if href:
                        logging.info(
                            "PURSUE_SEARCH bio_keyword_match idx=%d", idx
                        )
                        return href
            except Exception:
                continue

        # No bio match — fall back to the first result.
        try:
            link = profile_elements[0].find_element(
                By.XPATH, ".//a[contains(@href,'/in/')]"
            )
            return link.get_attribute("href")
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    # Connect button variants inside a people-search result card.
    _CONNECT_IN_CARD_SELECTORS = (
        ".//a[contains(@aria-label,'to connect')]",
        ".//a[contains(@href,'search-custom-invite')]",
        ".//button[contains(@aria-label,'to connect')]",
        ".//button[normalize-space()='Connect']",
        ".//button[.//span[normalize-space()='Connect']]",
    )

    def _people_search_url(self, query: str, page: int = 1) -> str:
        """LinkedIn people-search URL with optional ``page`` (1-based)."""
        encoded = urllib.parse.quote_plus(str(query).strip())
        url = (
            "https://www.linkedin.com/search/results/people/"
            f"?keywords={encoded}&origin=GLOBAL_SEARCH_HEADER"
        )
        if page > 1:
            url += f"&page={page}"
        return url

    def open_people_search(self, query: str, page: int = 1) -> bool:
        """Navigate to LinkedIn people search for ``query``."""
        if not query or not str(query).strip():
            return False
        query = str(query).strip()
        search_url = self._people_search_url(query, page=page)
        try:
            logging.info("CONNECT_SEARCH start query=%r page=%d", query, page)
            self.driver.get(search_url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[starts-with(@componentkey,'SearchResultsACo')]"
                        " | //a[contains(@href,'/in/')]",
                    )
                )
            )
            time.sleep(2.5)
            return True
        except Exception as exc:
            logging.warning("CONNECT_SEARCH navigation_failed: %s", exc)
            return False

    def _go_to_next_search_page(self, query: str, current_page: int) -> Optional[int]:
        """Open the next people-search results page. Returns new page number or None."""
        next_page = current_page + 1
        if next_page > 20:
            return None

        try:
            clicked = self.driver.execute_script(
                """
                const btn = document.querySelector(
                  'button[aria-label="Next"]:not([disabled]), '
                  + 'button.artdeco-pagination__button--next:not([disabled])'
                );
                if (btn) {
                  btn.scrollIntoView({ block: "center" });
                  btn.click();
                  return true;
                }
                return false;
                """
            )
            if clicked:
                time.sleep(2.5)
                logging.info("CONNECT advanced search_page=%d via_next_button", next_page)
                return next_page
        except Exception:
            pass

        try:
            self.driver.get(self._people_search_url(query, page=next_page))
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[starts-with(@componentkey,'SearchResultsACo')]"
                        " | //a[contains(@href,'/in/')]",
                    )
                )
            )
            time.sleep(2.5)
            logging.info("CONNECT advanced search_page=%d via_url", next_page)
            return next_page
        except Exception as exc:
            logging.warning("CONNECT next_page_failed page=%d err=%s", next_page, exc)
            return None

    def connect_people(
        self,
        query: str,
        max_connects: int = 10,
        note: Optional[str] = None,
        bio_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search people by keyword and send connection requests from results."""
        results: Dict[str, Any] = {
            "query": query,
            "sent": 0,
            "skipped": 0,
            "errors": [],
        }
        if max_connects <= 0:
            return results

        if not self.open_people_search(query):
            results["errors"].append("Could not open people search results")
            self._dump_pursue_diagnostics(reason="connect_search_failed", query=query)
            return results

        initial = self._wait_for_people_search_results(timeout=20, min_results=1)
        if not initial:
            results["errors"].append(
                "No connectable people found (all may be Pending or weekly limit reached)"
            )
            self._dump_pursue_diagnostics(reason="connect_no_connectable", query=query)
            return results
        logging.info("CONNECT search_results_ready connectable=%d", len(initial))

        if self._invitation_modal_visible():
            logging.info("CONNECT clearing leftover invitation modal before search")
            self._dismiss_connection_modal()
            time.sleep(0.5)

        seen_profiles: Set[str] = set()
        stalled = 0
        stall_budget = 8
        search_page = 1

        while results["sent"] < max_connects and stalled < stall_budget:
            targets = self._collect_people_profile_targets(bio_keywords)
            fresh = [
                t for t in targets
                if t.get("key") and t["key"] not in seen_profiles
            ]
            logging.info(
                "CONNECT connectable_visible=%d new=%d page=%d",
                len(targets),
                len(fresh),
                search_page,
            )
            progress = False

            if not fresh:
                next_page = self._go_to_next_search_page(query, search_page)
                if next_page:
                    search_page = next_page
                    stalled = 0
                    self._wait_for_people_search_results(timeout=12, min_results=0)
                    continue
                stalled += 1
                time.sleep(1.5)
                continue

            for target in fresh:
                if results["sent"] >= max_connects:
                    break

                profile_key = target.get("key")
                if not profile_key:
                    continue
                seen_profiles.add(profile_key)

                if self._invitation_modal_visible():
                    self._dismiss_connection_modal()

                click_status = self._click_connect_on_search_card(profile_key)
                if click_status == "pending":
                    results["skipped"] += 1
                    logging.info("CONNECT skip pending profile=%s", profile_key)
                    continue
                if click_status != "clicked":
                    results["skipped"] += 1
                    logging.info(
                        "CONNECT skip search_no_button profile=%s status=%s",
                        profile_key,
                        click_status,
                    )
                    continue

                time.sleep(0.8)
                if self._submit_connection_invitation(
                    note, profile_key=profile_key, search_query=query, search_page=search_page
                ):
                    results["sent"] += 1
                    progress = True
                    logging.info(
                        "CONNECT sent profile=%s total=%d",
                        profile_key,
                        results["sent"],
                    )
                    time.sleep(random.uniform(2.0, 4.0))
                else:
                    results["skipped"] += 1
                    logging.warning(
                        "CONNECT invite_not_completed profile=%s", profile_key
                    )
                    self._dismiss_connection_modal()
                    if query:
                        self._recover_people_search(query, page=search_page)

            if progress:
                stalled = 0
            else:
                next_page = self._go_to_next_search_page(query, search_page)
                if next_page:
                    search_page = next_page
                    stalled = 0
                    self._wait_for_people_search_results(timeout=12, min_results=0)
                else:
                    stalled += 1
                    time.sleep(1.5)

        if results["sent"] == 0 and not results["errors"]:
            self._dump_pursue_diagnostics(reason="connect_no_sent", query=query)

        return results

    def _extract_profile_targets_from_page(self) -> List[Dict[str, str]]:
        """People on the search page who still show a Connect / invite control."""
        raw: List[Dict[str, str]] = []
        try:
            extracted = self.driver.execute_script(
                """
                const seen = new Set();
                const out = [];
                const push = (key, url) => {
                  if (!key || seen.has(key)) return;
                  seen.add(key);
                  out.push({
                    key,
                    url: url || (`https://www.linkedin.com/in/${key}/`),
                  });
                };
                const isPendingCard = (card) => {
                  for (const el of card.querySelectorAll("span, button, a")) {
                    const t = (el.textContent || "").trim();
                    if (t === "Pending" || t === "Sent") return true;
                  }
                  return false;
                };
                const findConnect = (card) => {
                  if (isPendingCard(card)) return null;
                  const invite = card.querySelector(
                    "a[href*='search-custom-invite'], a[aria-label*='to connect']"
                  );
                  if (invite) return invite;
                  for (const span of card.querySelectorAll("span")) {
                    if ((span.textContent || "").trim() === "Connect") {
                      const el = span.closest("a, button, [role='button']");
                      if (el) return el;
                    }
                  }
                  return null;
                };
                for (const card of document.querySelectorAll(
                  "div[componentkey^='SearchResultsACo']"
                )) {
                  const connectEl = findConnect(card);
                  if (!connectEl) continue;

                  let key = null;
                  let url = null;
                  try {
                    const u = new URL(connectEl.href || "", location.origin);
                    key = u.searchParams.get("vanityName");
                  } catch (e) {}

                  const profile = card.querySelector("a[href*='/in/']");
                  if (profile) {
                    url = (profile.href || "").split("?")[0].split("#")[0];
                    if (!key) {
                      const m = url.match(/\\/in\\/([^/?#]+)/i);
                      if (m) key = m[1];
                    }
                  }
                  if (!key && connectEl.getAttribute("aria-label")) {
                    const m = connectEl.getAttribute("aria-label")
                      .match(/invite\\s+(.+?)\\s+to connect/i);
                    if (m) {
                      key = m[1].trim().toLowerCase().replace(/\\s+/g, "-");
                    }
                  }
                  if (key) push(key, url);
                }
                return out;
                """
            )
            if isinstance(extracted, list):
                raw = [x for x in extracted if isinstance(x, dict) and x.get("key")]
        except Exception as exc:
            logging.warning("CONNECT js_extract_failed: %s", exc)

        return raw

    def _wait_for_people_search_results(
        self, timeout: float = 20.0, min_results: int = 1
    ) -> List[Dict[str, str]]:
        """Poll until connectable people-search cards render or timeout."""
        deadline = time.time() + timeout
        last: List[Dict[str, str]] = []
        while time.time() < deadline:
            last = self._extract_profile_targets_from_page()
            if len(last) >= min_results:
                return last
            try:
                self.driver.execute_script(
                    "window.scrollBy(0, Math.min(window.innerHeight * 0.5, 600));"
                )
            except Exception:
                pass
            time.sleep(1.2)
        return last

    def _collect_people_profile_targets(
        self, bio_keywords: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """Collect unique profile URLs from the people-search page."""
        raw = self._extract_profile_targets_from_page()
        if not raw:
            raw = self._wait_for_people_search_results(timeout=8, min_results=1)

        if not bio_keywords:
            return raw

        normalized = [kw.lower() for kw in bio_keywords if kw]
        if not normalized:
            return raw

        filtered: List[Dict[str, str]] = []
        for target in raw:
            try:
                card = self.driver.find_element(
                    By.XPATH,
                    f"//a[contains(@href,'/in/{target['key']}')]/ancestor::div[starts-with(@componentkey,'SearchResults')][1]",
                )
                text = (card.text or "").lower()
            except Exception:
                text = target.get("key", "").lower()
            if any(kw in text for kw in normalized):
                filtered.append(target)
        return filtered or raw

    def _click_connect_on_search_card(self, profile_key: str) -> str:
        """Click the inline Connect control on the people-search results page."""
        try:
            status = self.driver.execute_script(
                """
                const key = arguments[0];
                const isPendingCard = (card) => {
                  for (const el of card.querySelectorAll("span, button, a")) {
                    const t = (el.textContent || "").trim();
                    if (t === "Pending" || t === "Sent") return true;
                  }
                  return false;
                };
                const cards = document.querySelectorAll(
                  "div[componentkey^='SearchResultsACo']"
                );
                for (const card of cards) {
                  const invite = card.querySelector(
                    `a[href*='search-custom-invite'][href*='${key}'], a[href*='vanityName=${key}']`
                  );
                  if (!invite) {
                    const profileLink = card.querySelector(`a[href*="/in/${key}"]`);
                    if (!profileLink) continue;
                  }
                  if (isPendingCard(card)) return "pending";

                  let connectEl = invite;
                  if (!connectEl) {
                    const profileLink = card.querySelector(`a[href*="/in/${key}"]`);
                    if (!profileLink) continue;
                    connectEl = card.querySelector(
                      "a[aria-label*='to connect'], a[href*='search-custom-invite'], button[aria-label*='to connect']"
                    );
                    if (!connectEl) {
                      for (const span of card.querySelectorAll("span")) {
                        if ((span.textContent || "").trim() === "Connect") {
                          connectEl = span.closest("a, button, [role='button']");
                          if (connectEl) break;
                        }
                      }
                    }
                  }
                  if (!connectEl) return "no_button";

                  connectEl.scrollIntoView({ block: "center" });
                  connectEl.click();
                  return "clicked";
                }
                return "not_found";
                """,
                profile_key,
            )
            if status == "clicked":
                logging.info("CONNECT clicked search_card profile=%s", profile_key)
            return str(status or "not_found")
        except Exception as exc:
            logging.warning(
                "CONNECT search_click_failed profile=%s err=%s", profile_key, exc
            )
            return "error"

    def _collect_people_search_cards(
        self, bio_keywords: Optional[List[str]]
    ) -> List[Any]:
        """Return visible people-search result cards, optionally bio-filtered."""
        profile_elements: List = []
        for selector in _RESULT_SELECTORS:
            try:
                els = self.driver.find_elements(By.XPATH, selector)
                if els:
                    profile_elements = els
                    break
            except Exception:
                continue

        if not profile_elements:
            profile_elements = self._cards_from_profile_anchors()

        if not bio_keywords:
            return profile_elements

        normalized = [kw.lower() for kw in bio_keywords if kw]
        if not normalized:
            return profile_elements

        filtered: List = []
        for el in profile_elements:
            try:
                text = (el.text or "").lower()
                if any(kw in text for kw in normalized):
                    filtered.append(el)
            except Exception:
                continue
        return filtered or profile_elements

    def _cards_from_profile_anchors(self) -> List[Any]:
        """Build result cards from visible /in/ links when container selectors miss."""
        cards: List[Any] = []
        seen: Set[str] = set()
        try:
            anchors = self.driver.find_elements(
                By.CSS_SELECTOR, "a[href*='/in/']"
            )
        except Exception:
            return cards

        for anchor in anchors:
            try:
                href = (anchor.get_attribute("href") or "").split("?", 1)[0]
                if "/in/" not in href:
                    continue
                vanity = href.rstrip("/").split("/in/", 1)[-1].split("/", 1)[0]
                if not vanity or vanity in seen:
                    continue
                seen.add(vanity)

                card = anchor
                for xp in (
                    "./ancestor::div[starts-with(@componentkey,'SearchResultsACo')][1]",
                    "./ancestor::li[.//a[contains(@href,'/in/')]][1]",
                    "./ancestor::div[.//a[contains(@href,'/in/')]][1]",
                ):
                    try:
                        card = anchor.find_element(By.XPATH, xp)
                        break
                    except Exception:
                        continue
                cards.append(card)
            except Exception:
                continue
        return cards

    def _profile_url_from_card(self, card) -> Optional[str]:
        """Return a normalized profile URL from a search-result card."""
        try:
            link = card.find_element(By.XPATH, ".//a[contains(@href,'/in/')]")
            href = (link.get_attribute("href") or "").split("?", 1)[0].split("#", 1)[0]
            if "/in/" in href:
                return href.rstrip("/") + "/"
        except Exception:
            pass
        return None

    def _profile_key_from_card(self, card) -> Optional[str]:
        """Stable dedupe key from a result card's /in/ profile link."""
        try:
            link = card.find_element(By.XPATH, ".//a[contains(@href,'/in/')]")
            href = (link.get_attribute("href") or "").split("?", 1)[0].split("#", 1)[0]
            if "/in/" in href:
                return href.rstrip("/").split("/in/", 1)[-1].split("/", 1)[0]
        except Exception:
            pass
        return None

    def _card_already_connected(self, card) -> bool:
        """True when the card shows an existing or pending connection."""
        try:
            text = (card.text or "").lower()
        except Exception:
            text = ""
        if "pending" in text:
            return True
        if re.search(r"\b[123](?:st|nd|rd)\b", text) and "degree" in text:
            return True
        if self._find_connect_button_in_card(card):
            return False
        for xp in (
            ".//button[normalize-space()='Message']",
            ".//button[contains(@aria-label,'Message')]",
        ):
            try:
                if card.find_elements(By.XPATH, xp):
                    return True
            except Exception:
                continue
        return False

    _CONNECT_PROFILE_SELECTORS = (
        "//main//button[@aria-label and contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'invite') and contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'connect')]",
        "//main//button[normalize-space()='Connect']",
        "//main//button[.//span[normalize-space()='Connect']]",
        "//main//button[contains(@aria-label,'Connect')]",
    )

    def _profile_already_connected(self) -> bool:
        """True when the open profile page shows an existing connection."""
        for xp in (
            "//main//button[normalize-space()='Pending']",
            "//main//button[.//span[normalize-space()='Pending']]",
            "//main//button[normalize-space()='Message']",
            "//main//button[contains(@aria-label,'Message')]",
            "//main//span[contains(text(),'1st degree connection')]",
            "//main//span[contains(text(),'2nd degree connection')]",
        ):
            try:
                if self.driver.find_elements(By.XPATH, xp):
                    return True
            except Exception:
                continue
        return False

    def _click_connect_on_profile(self) -> bool:
        """Click Connect on the currently open profile page."""
        for xp in self._CONNECT_PROFILE_SELECTORS:
            try:
                btn = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
            except Exception:
                continue
            label = (btn.get_attribute("aria-label") or btn.text or "").lower()
            if any(skip in label for skip in ("pending", "message", "following")):
                continue
            try:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", btn
                )
                time.sleep(0.3)
                self.driver.execute_script("arguments[0].click();", btn)
            except Exception:
                try:
                    btn.click()
                except Exception:
                    continue
            logging.info("CONNECT clicked profile_page selector=%s", xp)
            return True
        return False

    def _find_connect_button_in_card(self, card):
        """Return a clickable Connect button inside a search result card."""
        for xp in self._CONNECT_IN_CARD_SELECTORS:
            try:
                for btn in card.find_elements(By.XPATH, xp):
                    label = (
                        btn.get_attribute("aria-label") or btn.text or ""
                    ).lower()
                    if any(
                        skip in label
                        for skip in ("pending", "message", "following", "unfollow")
                    ):
                        continue
                    if "connect" in label or (btn.text or "").strip() == "Connect":
                        return btn
            except Exception:
                continue
        # LinkedIn 2026 search uses <a> invite links, not <button>.
        for xp in (
            ".//a[contains(@aria-label,'to connect')]",
            ".//a[contains(@href,'search-custom-invite')]",
        ):
            try:
                for link in card.find_elements(By.XPATH, xp):
                    label = (link.get_attribute("aria-label") or "").lower()
                    if "pending" in label or "message" in label:
                        continue
                    return link
            except Exception:
                continue
        return None

    def _click_xpath(self, xpaths: tuple[str, ...], log_label: str = "") -> bool:
        """Click the first matching visible XPath target."""
        for xp in xpaths:
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, xp))
                )
                if (el.tag_name or "").lower() == "span":
                    try:
                        el = el.find_element(By.XPATH, "./ancestor::button[1]")
                    except Exception:
                        pass
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", el
                )
                time.sleep(0.2)
                try:
                    el.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", el)
                if log_label:
                    logging.info("CONNECT clicked %s xpath=%s", log_label, xp[:80])
                return True
            except Exception:
                continue
        return False

    def _click_send_without_note_modal(self) -> bool:
        """Click Send without a note using artdeco modal button markup."""
        try:
            clicked = self.driver.execute_script(
                """
                for (const span of document.querySelectorAll(
                  "span.artdeco-button__text"
                )) {
                  const t = (span.textContent || "").replace(/\\s+/g, " ").trim();
                  if (!t.includes("Send without a note")) continue;
                  const btn = span.closest("button");
                  if (!btn) continue;
                  const r = btn.getBoundingClientRect();
                  if (r.width < 2 || r.height < 2) continue;
                  btn.scrollIntoView({ block: "center" });
                  btn.click();
                  return true;
                }
                return false;
                """
            )
            if clicked:
                logging.info("CONNECT clicked send_without_a_note via artdeco-button__text")
                return True
        except Exception as exc:
            logging.warning("CONNECT artdeco_send_click_failed: %s", exc)
        return self._click_xpath(
            _SEND_WITHOUT_NOTE_XPATHS, log_label="send_without_a_note"
        )

    def _invite_ui_present(self) -> bool:
        """True when the invitation modal or invite page is visible."""
        try:
            return bool(
                self.driver.execute_script(
                    """
                    const norm = (s) => (s || "").replace(/\\s+/g, " ").trim();
                    const hasInviteCopy = (root) => {
                      if (!root) return false;
                      const text = norm(root.innerText || root.textContent);
                      return text.includes("Add a note to your invitation")
                        || text.includes("Send without a note");
                    };
                    if (location.href.includes("search-custom-invite")) return true;
                    const outlet = document.querySelector("#artdeco-modal-outlet");
                    if (hasInviteCopy(outlet)) return true;
                    if (hasInviteCopy(document.body)) return true;
                    const walk = (node) => {
                      if (!node) return false;
                      if (hasInviteCopy(node)) return true;
                      if (node.shadowRoot && walk(node.shadowRoot)) return true;
                      for (const child of node.children || []) {
                        if (walk(child)) return true;
                      }
                      return false;
                    };
                    return walk(document.documentElement);
                    """
                )
            )
        except Exception:
            return False

    def _find_invite_action_js(self, label: str) -> bool:
        """Click a button/link on the invite modal by visible label."""
        try:
            return bool(
                self.driver.execute_script(
                    """
                    const label = arguments[0];
                    const norm = (s) => (s || "").replace(/\\s+/g, " ").trim();
                    const match = (el) => {
                      const t = norm(el.innerText || el.textContent);
                      const a = norm(el.getAttribute("aria-label"));
                      return t === label || a === label || t.includes(label);
                    };
                    const clickTarget = (el) => {
                      if (!el) return null;
                      const tag = (el.tagName || "").toLowerCase();
                      if (tag === "button" || tag === "a" || el.getAttribute("role") === "button") {
                        return el;
                      }
                      return el.closest("button, a, [role='button']");
                    };
                    const tryRoot = (root) => {
                      if (!root || !root.querySelectorAll) return null;
                      for (const el of root.querySelectorAll(
                        "button, a, [role='button'], span, div.artdeco-button"
                      )) {
                        if (!match(el)) continue;
                        const target = clickTarget(el);
                        if (!target) continue;
                        const r = target.getBoundingClientRect();
                        if (r.width < 2 || r.height < 2) continue;
                        target.scrollIntoView({ block: "center" });
                        target.click();
                        return true;
                      }
                      return null;
                    };
                    const roots = [
                      document.querySelector("#artdeco-modal-outlet"),
                      document.querySelector("[role='dialog']"),
                      document.querySelector(".artdeco-modal"),
                      document.body,
                    ].filter(Boolean);
                    for (const root of roots) {
                      if (tryRoot(root)) return true;
                    }
                    const walk = (node) => {
                      if (!node) return false;
                      if (tryRoot(node)) return true;
                      if (node.shadowRoot && walk(node.shadowRoot)) return true;
                      for (const child of node.children || []) {
                        if (walk(child)) return true;
                      }
                      return false;
                    };
                    return walk(document.documentElement);
                    """
                    ,
                    label,
                )
            )
        except Exception:
            return False

    def _wait_and_click_invite_action(self, label: str, timeout: float = 18) -> bool:
        """Poll until an invite modal action (e.g. Send without a note) is clickable."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if "Send without a note" in label and self._click_send_without_note_modal():
                return True
            if self._find_invite_action_js(label):
                return True
            time.sleep(0.4)
        return False

    def _wait_for_invite_ui(self, timeout: float = 10) -> bool:
        """Poll until the invitation modal or invite page appears."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._invite_ui_present():
                return True
            time.sleep(0.4)
        return False

    def _open_invite_for_profile(self, profile_key: str) -> bool:
        """Open the custom-invite UI for a profile vanity slug."""
        invite_url = (
            "https://www.linkedin.com/preload/search-custom-invite/"
            f"?vanityName={urllib.parse.quote(profile_key)}"
        )
        try:
            self.driver.get(invite_url)
            time.sleep(1.5)
            return self._invite_ui_present() or self._wait_and_click_invite_action(
                "Send without a note", timeout=8
            )
        except Exception as exc:
            logging.warning("CONNECT invite_url_open_failed profile=%s err=%s", profile_key, exc)
            return False

    def _recover_people_search(self, query: str, page: int = 1) -> None:
        """Return to the people-search results page after handling an invite."""
        try:
            if "search/results/people" not in (self.driver.current_url or ""):
                self.driver.get(self._people_search_url(query, page=page))
                time.sleep(2.0)
        except Exception:
            pass

    def _send_without_note_present(self) -> bool:
        """True when the Send-without-a-note control is visible."""
        if self._find_send_without_note_button() is not None:
            return True
        try:
            return bool(
                self.driver.execute_script(
                    """
                    const norm = (s) => (s || "").replace(/\\s+/g, " ").trim();
                    for (const el of document.querySelectorAll(
                      "button, [role='button'], a, div, span"
                    )) {
                      const t = norm(el.innerText || el.textContent);
                      if (t === "Send without a note" || t.includes("Send without a note")) {
                        const r = el.getBoundingClientRect();
                        if (r.width > 0 && r.height > 0) return true;
                      }
                    }
                    return false;
                    """
                )
            )
        except Exception:
            return False

    def _find_send_without_note_button(self):
        """Return the visible Send-without-a-note button, if any."""
        xpaths = (
            "//div[@role='dialog']//button[contains(normalize-space(.), 'Send without a note')]",
            "//button[.//span[normalize-space()='Send without a note']]",
            "//button[contains(normalize-space(.), 'Send without a note')]",
            "//*[@role='button' and contains(normalize-space(.), 'Send without a note')]",
            "//span[normalize-space()='Send without a note']/ancestor::button[1]",
        )
        for xp in xpaths:
            try:
                for el in self.driver.find_elements(By.XPATH, xp):
                    try:
                        if el.is_displayed():
                            return el
                    except Exception:
                        return el
            except Exception:
                continue
        for xp in xpaths:
            try:
                els = self.driver.find_elements(By.XPATH, xp)
                if els:
                    return els[0]
            except Exception:
                continue
        return None

    def _invitation_modal_visible(self) -> bool:
        """True when LinkedIn's post-Connect invitation modal is on screen."""
        return self._invite_ui_present()

    def _wait_invitation_modal_closed(self, timeout: float = 8) -> bool:
        """Wait until the invitation modal is gone."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda _: not self._invite_ui_present()
            )
            return True
        except Exception:
            return False

    def _click_send_without_note(self) -> bool:
        """Click the Send-without-a-note button in the invitation modal."""
        if self._click_send_without_note_modal():
            return True
        if self._find_invite_action_js("Send without a note"):
            return True
        return self._find_send_without_note_button() is not None and self._click_send_without_note_legacy()

    def _click_send_without_note_legacy(self) -> bool:
        """Legacy Selenium click path for Send-without-a-note."""
        btn = self._find_send_without_note_button()
        if btn is None:
            return False
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", btn
            )
            time.sleep(0.2)
            try:
                btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", btn)
            return True
        except Exception as exc:
            logging.warning("CONNECT send_without_note_click_failed: %s", exc)
            return False

    def _submit_connection_invitation(
        self,
        note: Optional[str],
        profile_key: Optional[str] = None,
        search_query: Optional[str] = None,
        search_page: int = 1,
    ) -> bool:
        """Complete the post-click invitation modal (with or without a note)."""
        trimmed = (note or "").strip()
        time.sleep(0.6)

        if not self._wait_for_invite_ui(timeout=8):
            if profile_key and self._open_invite_for_profile(profile_key):
                logging.info("CONNECT opened invite_url profile=%s", profile_key)
            elif not self._wait_for_invite_ui(timeout=8):
                logging.warning(
                    "CONNECT invite_ui_timed_out url=%s",
                    self.driver.current_url,
                )
                return False

        if trimmed:
            if not self._find_invite_action_js("Add a note"):
                logging.warning("CONNECT add_note_button_not_found")
                return False
            time.sleep(0.5)

            for xp in (
                "//div[@role='dialog']//textarea",
                "//textarea[contains(@id,'custom-message')]",
                "//textarea[@name='message']",
                "//textarea",
            ):
                try:
                    ta = WebDriverWait(self.driver, 4).until(
                        EC.presence_of_element_located((By.XPATH, xp))
                    )
                    ta.clear()
                    ta.send_keys(trimmed[:300])
                    break
                except Exception:
                    continue

            if not self._wait_and_click_invite_action("Send", timeout=8):
                return False
            closed = self._wait_invitation_modal_closed()
            if search_query:
                self._recover_people_search(search_query, page=search_page)
            return closed

        if not self._wait_and_click_invite_action("Send without a note", timeout=15):
            logging.warning(
                "CONNECT send_without_note_not_found url=%s",
                self.driver.current_url,
            )
            return False

        logging.info("CONNECT clicked send_without_a_note")
        if not self._wait_invitation_modal_closed():
            logging.warning("CONNECT invite_modal_still_open_after_send")
            return False
        if search_query:
            self._recover_people_search(search_query, page=search_page)
        return True

    def _dismiss_connection_modal(self) -> None:
        """Close any leftover invitation modal so the next search click works."""
        if not self._invite_ui_present():
            return

        if self._click_send_without_note_modal():
            self._wait_invitation_modal_closed(timeout=3)
            return
        if self._find_invite_action_js("Send without a note"):
            self._wait_invitation_modal_closed(timeout=3)
            return

        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.4)
        except Exception:
            pass

        if self._find_invite_action_js("Dismiss"):
            return

        for xp in (
            "//div[@role='dialog']//button[@aria-label='Dismiss']",
            "//div[@role='dialog']//button[contains(@aria-label,'Close')]",
            "//button[@aria-label='Dismiss']",
            "//button[contains(@aria-label,'Close')]",
        ):
            try:
                btn = WebDriverWait(self.driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.3)
                return
            except Exception:
                continue

    def _dump_pursue_diagnostics(self, reason: str, query: str) -> None:
        """Save HTML + PNG when search fails so we can post-mortem reliably.

        Mirrors engage_flow._dump_diagnostics. Best-effort; never raises.
        """
        try:
            os.makedirs(_DIAG_DIR, exist_ok=True)
            stamp = time.strftime("%Y%m%d_%H%M%S")
            slug = f"pursue_{reason}_{stamp}"

            try:
                url = self.driver.current_url
            except Exception:
                url = "<unavailable>"
            try:
                title = self.driver.title
            except Exception:
                title = "<unavailable>"
            logging.info(
                "PURSUE_DIAG reason=%s query=%r url=%s title=%r dir=%s",
                reason,
                query,
                url,
                title,
                _DIAG_DIR,
            )

            html_path = os.path.join(_DIAG_DIR, f"{slug}.html")
            png_path = os.path.join(_DIAG_DIR, f"{slug}.png")

            try:
                with open(html_path, "w", encoding="utf-8") as fh:
                    fh.write(self.driver.page_source or "")
                logging.info("PURSUE_DIAG saved_html=%s", html_path)
            except Exception as exc:
                logging.warning("PURSUE_DIAG html_dump_failed: %s", exc)

            try:
                self.driver.save_screenshot(png_path)
                logging.info("PURSUE_DIAG saved_png=%s", png_path)
            except Exception as exc:
                logging.warning("PURSUE_DIAG screenshot_failed: %s", exc)
        except Exception as exc:
            logging.warning("PURSUE_DIAG dump_failed: %s", exc)

    # Selectors for the Follow / Following primary action on a profile page.
    # LinkedIn shows several variants depending on relationship + viewer type
    # (e.g. Top Voice, 1st degree connection, restricted profile, mobile A/B).
    _FOLLOW_BUTTON_SELECTORS = (
        # The dedicated aria-labelled button — most reliable when present.
        "//button[@aria-label and starts-with(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'follow ')]",
        "//button[@aria-label and translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='follow']",
        # Visible label match — handles the post-2024 layouts where the
        # button has just text and no aria-label.
        "//button[normalize-space()='Follow']",
        "//button[.//span[normalize-space()='Follow']]",
        # Generic fallback — any button whose text contains "Follow" but
        # NOT "Following" (we filter at the Python level too).
        "//button[.//*[contains(text(),'Follow')] and not(.//*[contains(text(),'Following')])]",
    )

    # "More" overflow toggle on the profile header. For Top Voices / public
    # figures LinkedIn hides Follow behind this menu and shows Connect /
    # Message as the primary actions instead.
    _MORE_TOGGLE_SELECTORS = (
        "//main//button[@aria-label='More actions']",
        "//main//button[contains(@aria-label,'More actions')]",
        "//main//button[normalize-space()='More']",
        "//main//button[.//span[normalize-space()='More']]",
    )

    # Per-selector budget. Keep low — on a fully-rendered profile page the
    # button is either there immediately or not at all. The previous 5s ×
    # 5 selectors = 25 s wall time was wasted on every miss.
    _FOLLOW_WAIT_SEC = 1.5

    def follow_profile(self) -> bool:
        """Follow the current profile if not already following.

        Returns ``True`` when we actually clicked Follow, ``False`` when the
        viewer is already following, when no Follow button is reachable on
        this profile variant, or when an error occurs. Errors are logged at
        ``warning`` level (not ``error``) because being unable to follow is
        non-fatal for the pursue flow — we still want to engage with posts.

        Strategy (in order, all very fast):
          1. Fast-path: "Following" button visible → already following.
          2. Top-level Follow button (5 selector variants).
          3. Expand the "More" dropdown — Top Voices and public figures
             keep Follow hidden there and show Connect as the primary CTA.
        """
        # Fast-path: already-following button visible on the page.
        for xp in (
            "//button[normalize-space()='Following']",
            "//button[.//span[normalize-space()='Following']]",
        ):
            try:
                if self.driver.find_elements(By.XPATH, xp):
                    logging.info("FOLLOW skip already_following")
                    return False
            except Exception:
                continue

        if self._try_click_follow(self._FOLLOW_BUTTON_SELECTORS, source="top"):
            return True

        # No top-level Follow — try the "More" overflow dropdown.
        if self._open_profile_more_menu():
            if self._try_click_follow(
                self._FOLLOW_BUTTON_SELECTORS, source="more_menu"
            ):
                return True
            # Inside the dropdown items don't always render as <button>; they
            # frequently use role=menuitem on a <div>/<span>. Cover that too.
            for xp in (
                "//div[@role='menuitem' and .//span[normalize-space()='Follow']]",
                "//*[(self::div or self::a or self::li) and @role='menuitem' and (normalize-space()='Follow' or .//span[normalize-space()='Follow'])]",
            ):
                try:
                    item = WebDriverWait(self.driver, self._FOLLOW_WAIT_SEC).until(
                        EC.element_to_be_clickable((By.XPATH, xp))
                    )
                except Exception:
                    continue
                try:
                    self.driver.execute_script("arguments[0].click();", item)
                except Exception:
                    try:
                        item.click()
                    except Exception:
                        continue
                logging.info("FOLLOW clicked source=more_menu_role_menuitem")
                time.sleep(0.8)
                return True

        logging.warning("FOLLOW no_follow_button_found")
        return False

    def _try_click_follow(self, selectors, source: str) -> bool:
        """Attempt to click any of the given XPath Follow selectors."""
        for xp in selectors:
            try:
                btn = WebDriverWait(self.driver, self._FOLLOW_WAIT_SEC).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
            except Exception:
                continue
            text = (btn.text or "").strip().lower()
            if "following" in text:
                logging.info("FOLLOW skip already_following (button text)")
                return False
            try:
                self.driver.execute_script("arguments[0].click();", btn)
            except Exception:
                try:
                    btn.click()
                except Exception as exc:
                    logging.warning(
                        "FOLLOW click_failed source=%s err=%s", source, exc
                    )
                    continue
            logging.info("FOLLOW clicked source=%s", source)
            time.sleep(0.8)
            return True
        return False

    def _open_profile_more_menu(self) -> bool:
        """Click the profile header's "More" dropdown so its items render."""
        for xp in self._MORE_TOGGLE_SELECTORS:
            try:
                toggle = WebDriverWait(self.driver, self._FOLLOW_WAIT_SEC).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
            except Exception:
                continue
            try:
                self.driver.execute_script("arguments[0].click();", toggle)
            except Exception:
                try:
                    toggle.click()
                except Exception:
                    continue
            logging.info("FOLLOW opened_more_menu selector=%s", xp)
            time.sleep(0.5)
            return True
        return False

    def open_profile_posts_view(self) -> bool:
        """Land on the profile's ``/recent-activity/all/`` page.

        We previously clicked a "Show all posts" link inside the profile
        page, but LinkedIn frequently flips the class names + label on that
        link (and sometimes hides it entirely behind a viewer-state check).
        Direct navigation is far more reliable: the URL is stable and the
        result is always a feed-shaped page our ``_find_visible_posts``
        selectors already understand.
        """
        try:
            current_url = self.driver.current_url or ""
            if "recent-activity" in current_url:
                return True

            # Derive the recent-activity URL from whichever profile URL we
            # currently sit on. We slice up to ``/in/<vanity>/`` so query
            # strings / detail-page suffixes don't leak in.
            target = current_url.split("?", 1)[0].split("#", 1)[0]
            if "/in/" not in target:
                logging.warning(
                    "PURSUE_POSTS_VIEW current_url_not_a_profile=%s", current_url
                )
                return False
            if not target.endswith("/"):
                target += "/"
            target += "recent-activity/all/"

            try:
                self.driver.get(target)
            except Exception as exc:
                logging.warning("PURSUE_POSTS_VIEW navigation_failed: %s", exc)
                return False

            # Wait for at least one feed-style post container OR for the URL
            # to confirm the navigation. Either is enough to proceed.
            try:
                WebDriverWait(self.driver, 12).until(
                    lambda d: "recent-activity" in (d.current_url or "")
                )
            except Exception:
                pass
            try:
                WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//div[contains(@class,'feed-shared-update-v2')] | //div[@data-id] | //div[contains(@class,'fie-impression-container')]",
                        )
                    )
                )
            except Exception:
                # No posts yet rendered — caller's engage loop will keep
                # scrolling. Still treat the navigation as successful so we
                # don't pointlessly retry the same URL.
                pass

            logging.info("PURSUE_POSTS_VIEW landed=%s", target)
            return True
        except Exception as e:
            logging.error(f"Error opening profile posts view: {str(e)}")
            return False

    def get_profile_post_urls(self, max_posts: int = 5) -> List[str]:
        """Get URLs of the most recent posts from the current profile.

        Args:
            max_posts: Maximum number of post URLs to return

        Returns:
            List of post URLs (up to max_posts)
        """
        try:
            self.open_profile_posts_view()

            last_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )
            post_urls: set[str] = set()

            while len(post_urls) < max_posts:
                posts = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "a.app-aware-link[href*='/posts/'], a.app-aware-link[href*='/recent-activity/']",
                )

                for post in posts:
                    href = post.get_attribute("href")
                    if href and "/posts/" in href and href not in post_urls:
                        post_urls.add(href)
                        if len(post_urls) >= max_posts:
                            break

                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(2)

                new_height = self.driver.execute_script(
                    "return document.body.scrollHeight"
                )
                if new_height == last_height:
                    try:
                        self.driver.execute_script(
                            "window.scrollTo(0, Math.max(document.body.scrollHeight - window.innerHeight, 0));"
                        )
                    except Exception:
                        pass
                    time.sleep(1.5)
                    new_height = self.driver.execute_script(
                        "return document.body.scrollHeight"
                    )
                    if new_height == last_height:
                        break
                last_height = new_height

            return list(post_urls)[:max_posts]

        except Exception as e:
            logging.error(f"Error getting profile posts: {str(e)}")
            return []

    def engage_profile_posts(
        self,
        max_posts: int,
        should_like: bool = True,
        should_comment: bool = True,
        comment_generator: Optional[Callable[[Any], Optional[str]]] = None,
        mention_author: bool = True,
        mention_position: str = "prepend",
    ) -> Dict[str, Any]:
        """Interact with visible posts on the current profile page."""
        results: Dict[str, Any] = {
            "posts_engaged": 0,
            "likes": 0,
            "comments": 0,
            "skipped": 0,
            "errors": [],
        }

        if max_posts <= 0:
            return results

        seen_keys: Set[str] = set()
        stalled = 0
        empty_initial = 0  # consecutive iterations where 0 posts were seen
        # Bail early when we never see *any* posts after a few scrolls — on a
        # static / restricted profile the page height won't change and we'd
        # otherwise loop the full ``stalled<8`` budget for nothing.
        EMPTY_BAIL = 3
        STALL_BUDGET = 5  # was 8 — too generous for a non-feed page

        while results["posts_engaged"] < max_posts and stalled < STALL_BUDGET:
            try:
                posts = self._find_visible_posts(limit=12)
            except Exception as err:
                logging.error(f"Error locating profile posts: {err}")
                results["errors"].append(f"Locate posts failed: {err}")
                posts = []

            if not posts:
                stalled += 1
                empty_initial += 1
                if empty_initial >= EMPTY_BAIL and not seen_keys:
                    logging.warning(
                        "PURSUE_ENGAGE bailing_no_posts_after=%d viewports",
                        empty_initial,
                    )
                    self._dump_pursue_diagnostics(
                        reason="profile_no_posts",
                        query=self.driver.current_url or "<unknown>",
                    )
                    break
                try:
                    self._scroll_feed(0.8, 1.6)
                except Exception:
                    self.driver.execute_script(
                        "window.scrollBy(0, window.innerHeight * 0.9);"
                    )
                time.sleep(1.2)
                continue

            progress = False

            for post in posts:
                if results["posts_engaged"] >= max_posts:
                    break

                try:
                    urn = self._extract_post_urn(post)
                    key = self._post_dedupe_key(post, urn)
                except Exception:
                    key = str(id(post))

                if key in seen_keys:
                    continue
                seen_keys.add(key)

                try:
                    if self._is_promoted_post(post):
                        results["skipped"] += 1
                        continue
                except Exception:
                    pass

                try:
                    action_bar = post.find_element(
                        By.XPATH,
                        ".//div[contains(@class,'feed-shared-social-action-bar')]",
                    )
                except Exception:
                    results["skipped"] += 1
                    continue

                acted = False

                if should_like:
                    try:
                        if self._like_from_bar(action_bar):
                            results["likes"] += 1
                            acted = True
                            time.sleep(1.0)
                    except Exception as err:
                        logging.error(f"Error liking profile post: {err}")
                        results["errors"].append(f"Like failed: {err}")

                if (
                    should_comment
                    and results["posts_engaged"] + (1 if acted else 0) < max_posts
                ):
                    comment_text = (
                        comment_generator(post) if comment_generator else None
                    )
                    if comment_text:
                        try:
                            if self._comment_from_bar(
                                action_bar,
                                comment_text,
                                mention_author=mention_author,
                                mention_position=mention_position,
                            ):
                                results["comments"] += 1
                                acted = True
                                time.sleep(2.0)
                        except Exception as err:
                            logging.error(f"Error commenting on profile post: {err}")
                            results["errors"].append(f"Comment failed: {err}")

                if acted:
                    progress = True
                    results["posts_engaged"] += 1
                    time.sleep(1.0)
                else:
                    results["skipped"] += 1

            if progress:
                stalled = 0
            else:
                stalled += 1
                try:
                    self._scroll_feed(0.8, 1.6)
                except Exception:
                    self.driver.execute_script(
                        "window.scrollBy(0, window.innerHeight * 0.9);"
                    )
                time.sleep(1.2)

        return results

    def like_post(self) -> bool:
        """Like the current post if not already liked.

        Returns:
            bool: True if liked, False if already liked or error
        """
        try:
            # Find the main post container
            post_container = self.driver.find_element(
                By.CSS_SELECTOR, "div.feed-shared-update-v2"
            )

            # Find the action bar
            action_bar = post_container.find_element(
                By.CSS_SELECTOR, "div.social-details-social-actions"
            )

            # Use the _like_from_bar method from EngageDomMixin
            return self._like_from_bar(action_bar)

        except Exception as e:
            logging.error(f"Error in like_post: {str(e)}")
            return False

    def comment_on_post(
        self,
        comment_text: str,
        mention_author: bool = False,
        mention_position: str = "append",
    ) -> bool:
        """Add a comment to the current post.

        Args:
            comment_text: Text of the comment to post
            mention_author: Whether to mention the post author in the comment
            mention_position: Where to place the mention ('prepend' or 'append')

        Returns:
            bool: True if comment was posted, False otherwise
        """
        try:
            # Find the main post container
            post_container = self.driver.find_element(
                By.CSS_SELECTOR, "div.feed-shared-update-v2"
            )

            # Find the action bar
            action_bar = post_container.find_element(
                By.CSS_SELECTOR, "div.social-details-social-actions"
            )

            # Use the _comment_from_bar method from EngageDomMixin
            return self._comment_from_bar(
                action_bar,
                comment_text,
                mention_author=mention_author,
                mention_position=mention_position,
            )

        except Exception as e:
            logging.error(f"Error in comment_on_post: {str(e)}")
            return False
