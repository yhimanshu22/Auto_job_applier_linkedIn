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
