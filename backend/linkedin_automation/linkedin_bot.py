"""High-level controller for orchestrating LinkedIn automation workflows.

Why:
    Provide a cohesive object that wires the browser driver, content
    generation, AI helpers, and UI interaction mixins so callers interact with
    a single abstraction.

When:
    Instantiated by CLI scripts or tests whenever posting content, scheduling,
    or engaging with the feed is required.

How:
    Sets up Selenium via :class:`DriverFactory`, configures AI clients,
    delegates UI operations to :class:`linkedin_ui.LinkedInInteraction`, and
    exposes convenience methods for posting custom text, processing topic files,
    and engaging with feed items.
"""

import os
import re
import json
import time
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from . import config

# Subsystem imports (DriverFactory, ContentGenerator, OpenAIClient,
# LinkedInInteraction, PostExtractor, ``selenium.By``) are **deferred** to
# :meth:`__init__` and the methods that need them. This keeps importing this
# module cheap — critical for fast subprocess cold-start and for paths like
# ``generate-calendar`` that don't need a browser at all.


class LinkedInBot:
    """Composite orchestrator that drives LinkedIn automation flows.

    Why:
        Aggregate driver management, content generation, and UI interactions so
        upstream callers focus on workflow intent rather than wiring.

    When:
        Create once per CLI invocation or integration test to handle posting or
        engagement tasks; the instance remains valid until :meth:`close` runs.

    How:
        Initialises Selenium via :class:`DriverFactory`, loads AI helpers, wraps
        the UI mixins through :class:`LinkedInInteraction`, and exposes helper
        methods that chain these subsystems together.
    """

    def __init__(
        self, use_openai: bool = True, requires_browser: bool = True
    ) -> None:
        """Instantiate the bot, optionally bringing up Selenium + LinkedIn login.

        Why:
            Many workflows need an authenticated browser session and want it
            ready before the first call. Some don't (e.g. content calendar
            generation talks only to AI), and they save several seconds by
            skipping driver setup and login.

        When:
            Called whenever a new automation run is needed. A fresh instance is
            recommended per run to avoid stale browser state.

        How:
            When ``requires_browser`` is True, spins up Selenium via
            :class:`DriverFactory`, builds :class:`ContentGenerator` /
            :class:`OpenAIClient`, wires :class:`LinkedInInteraction` and
            :class:`PostExtractor`, then logs in. When False, only the AI
            helpers are constructed and the browser is never launched.
            Subsystem imports happen lazily here so paths that don't need
            them never pay the import cost.

        Args:
            use_openai (bool): Toggle for initialising the OpenAI client; useful
                for offline or no-AI scenarios.
            requires_browser (bool): When False, skips driver setup and
                LinkedIn login. Used by browser-free commands like
                ``generate-calendar``.
        """
        # Always needed (lightweight after this module's deferred imports).
        from .content_generator import ContentGenerator

        self.content_generator = ContentGenerator()

        if use_openai and config.has_linkedin_llm_credentials():
            from .openai_client import OpenAIClient

            self.openai_client = OpenAIClient()
        else:
            self.openai_client = None

        if not requires_browser:
            # Browser-free path: leave driver / interaction unset. Methods
            # that need them will raise ``AttributeError`` if misused.
            self.driver = None
            self.linkedin = None
            self.post_extractor = None
            self._login_succeeded = True
            return

        # Browser-dependent subsystems: heavy imports start here.
        from .driver import DriverFactory
        from .linkedin_interaction import LinkedInInteraction
        from .linkedin_ui.post_extractor import PostExtractor

        self.driver = DriverFactory.setup_driver()
        self.linkedin = LinkedInInteraction(self.driver)
        self.post_extractor = PostExtractor(self.driver)

        # Login to LinkedIn (cookie pickle or credentials).
        self._login_succeeded = bool(self.linkedin.login())
        if not self._login_succeeded:
            logging.error(
                "LinkedIn login did not complete (wrong credentials, 2FA, closed "
                "browser window, or Chrome crashed). Keep the automation window open "
                "until login finishes; set HEADLESS=false for feed runs. Downstream "
                "browser steps will be skipped where possible."
            )

    def _get_random_perspective(self, perspectives: List[str]) -> str:
        """Select a perspective token for AI comment generation.

        Why:
            Ensures the engage stream rotates through varied tones (funny,
            motivational, insightful) without duplicating logic across call
            sites.

        When:
            Used internally when constructing AI prompts for engagement flows.

        How:
            Normalises the input list, replaces ``"random"`` with the default
            pool, and returns a random choice.

        Args:
            perspectives (list[str]): Candidate perspective labels, possibly
                including ``"random"``.

        Returns:
            str: A concrete perspective ready for prompt building.
        """
        standard_perspectives = ["funny", "motivational", "insightful"]

        if not perspectives or "random" in perspectives:
            if perspectives == ["random"]:
                return random.choice(standard_perspectives)

            valid_perspectives = [p for p in perspectives if p != "random"]
            return random.choice(valid_perspectives or standard_perspectives)

        return random.choice(perspectives)

    def process_topics(
        self,
        topic_file_path: Optional[str] = None,
        image_directory: Optional[str] = None,
        schedule_date: Optional[str] = None,
        schedule_time: Optional[str] = None,
        engage_with_feed: bool = False,
        max_posts_to_engage: int = 3,
        perspectives: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Publish a post sourced from a topics file and optionally engage feed posts.

        Why:
            Automates daily posting by drawing from a backlog of ideas while also
            kicking off lightweight engagement to boost reach.

        When:
            Triggered by the default CLI flow or schedulers that process topic
            queues at regular intervals.

        How:
            Loads topics (falling back to defaults), generates content via
            :class:`ContentGenerator`, selects media, posts via
            :class:`LinkedInInteraction`, optionally runs the engage stream, and
            trims the processed topic from the source file.

        Args:
            topic_file_path (str | None): Path to a newline-delimited topic file
                or ``None`` to use built-in templates.
            image_directory (str | None): Folder containing candidate images.
            schedule_date (str | None): Optional date string for scheduled posts.
            schedule_time (str | None): Optional time string for scheduled posts.
            engage_with_feed (bool): Whether to follow up with feed engagement.
            max_posts_to_engage (int): Maximum feed items to touch during
                engagement.
            perspectives (list[str] | None): Preferred AI perspectives for
                comments if engagement is enabled.

        Returns:
            dict: Outcome metadata including posting success and engagement
            stats.
        """
        if perspectives is None:
            perspectives = ["funny", "motivational", "insightful"]
        elif isinstance(perspectives, str):
            perspectives = [perspectives]

        results: Dict[str, Any] = {
            "post_created": False,
            "post_url": None,
            "engagement": None,
            "perspectives_used": [],
        }

        topic_file_path = topic_file_path or config.DEFAULT_TOPIC_FILE
        logging.info(
            f"Processing topics from {topic_file_path or 'built-in templates'}"
        )

        try:
            topics: List[str] = []
            topics_file_exists = False

            if topic_file_path and Path(topic_file_path).exists():
                topics_file_exists = True
                with open(topic_file_path, "r") as f:
                    topics = [t.strip() for t in f.readlines() if t.strip()]

            if topics:
                chosen_topic = random.choice(topics)
                logging.info(f"Found {len(topics)} topics. Selected: {chosen_topic}")
            else:
                default_topics = getattr(
                    self.content_generator,
                    "_default_posts",
                    {
                        "leadership",
                        "productivity",
                        "technology",
                        "networking",
                        "remote work",
                        "iot",
                        "ai",
                        "blockchain",
                    },
                )
                chosen_topic = random.choice(list(default_topics))
                logging.info(
                    f"No topics file found. Using built-in topic: {chosen_topic}"
                )

            # Generate content
            post_content = self.content_generator.generate_post_content(chosen_topic)

            if config.ENABLE_TEXT_PREPROCESSING:
                from .text_utils import preprocess_for_ai

                post_content = preprocess_for_ai(
                    post_content,
                    summarize_ratio=(
                        config.SUMMARIZE_RATIO if config.SUMMARIZE_INPUT else None
                    ),
                    max_chars=config.MAX_INPUT_CHARS,
                )

            images_to_post = self._select_images(image_directory)

            if self.linkedin.login():
                post_success = self.linkedin.post_to_linkedin(
                    post_content,
                    image_paths=images_to_post,
                    schedule_date=schedule_date,
                    schedule_time=schedule_time,
                )
                results["post_created"] = post_success

                if post_success and engage_with_feed:
                    logging.info("Post successful. Engaging with feed...")
                    try:
                        engagement_results = self.linkedin.engage_stream(
                            mode="comment",
                            comment_text=config.LINKEDIN_COMMENT_FALLBACK,
                            max_actions=max_posts_to_engage,
                            include_promoted=False,
                            ai_client=self.openai_client,
                            post_extractor=self.post_extractor,
                            ai_perspectives=perspectives,
                            ai_max_tokens=150,
                            ai_temperature=0.7,
                        )
                        results["engagement"] = {
                            "success": True,
                            "count": engagement_results.get("count", 0),
                            "errors": engagement_results.get("errors", []),
                            "perspectives_used": perspectives[
                                : engagement_results.get("count", 0)
                            ],
                        }
                    except Exception as e:
                        logging.error(f"Error engaging with feed: {e}")
                        results["engagement"] = {"success": False, "error": str(e)}

                if post_success and topics_file_exists and chosen_topic in topics:
                    self._update_topics_file(topic_file_path, topics, chosen_topic)

            time.sleep(random.uniform(5, 10))

        except Exception:
            logging.error("An error occurred while processing topics.", exc_info=True)

        return results

    def generate_content_calendar(
        self, niche: str, output_file: str, total_posts: int = 30
    ) -> None:
        """Generate a content calendar and save it to a file.

        Why:
            CLI command handler for creating a backlog of topics.

        Args:
            niche (str): Industry/niche.
            output_file (str): Path to save the topics.
            total_posts (int): Count of topics to generate.
        """
        topics = self.content_generator.generate_content_calendar(niche, total_posts)
        if topics:
            try:
                path = Path(output_file)
                # Append if exists, or create new
                mode = "a" if path.exists() else "w"
                with open(path, mode, encoding="utf-8") as f:
                    if mode == "a":
                        f.write("\n")
                    f.write("\n".join(topics))
                logging.info(
                    f"Successfully wrote {len(topics)} topics to {output_file}"
                )
            except Exception as e:
                logging.error(f"Failed to write calendar to file: {e}")
        else:
            logging.warning("No topics were generated.")

    def post_custom_text(
        self,
        post_text: str,
        image_directory: Optional[str] = None,
        mention_anchors: Optional[List[str]] = None,
        mention_names: Optional[List[str]] = None,
        image_paths: Optional[List[str]] = None,
        schedule_date: Optional[str] = None,
        schedule_time: Optional[str] = None,
    ) -> bool:
        """Publish a caller-supplied post with optional media and mentions.

        Why:
            Supports ad-hoc messaging outside the topic workflow while reusing
            the same resilient Selenium interactions.

        When:
            Used by CLI `--post-text` runs or tests wanting deterministic
            content.

        How:
            Validates input, injects inline mention placeholders, gathers media
            (explicit paths first, then directory sampling), ensures login, and
            delegates posting to :meth:`LinkedInInteraction.post_to_linkedin`.

        Args:
            post_text (str): Content to publish.
            image_directory (str | None): Folder to sample images from when
                ``image_paths`` is empty.
            mention_anchors (list[str] | None): Text anchors preceding mentions.
            mention_names (list[str] | None): Display names matching anchors.
            image_paths (list[str] | None): Explicit file paths to attach.
            schedule_date (str | None): Optional scheduling date.
            schedule_time (str | None): Optional scheduling time.

        Returns:
            bool: ``True`` on apparent success, ``False`` otherwise.
        """
        try:
            if not isinstance(post_text, str) or not post_text.strip():
                logging.error("post_custom_text requires a non-empty post_text string")
                return False

            processed_text = self._apply_anchor_mentions(
                post_text, mention_anchors, mention_names
            )
            images_to_post = [
                str(Path(p).absolute()) for p in (image_paths or []) if Path(p).exists()
            ]
            if not images_to_post:
                images_to_post = self._select_images(image_directory)

            if not self.linkedin.login():
                logging.error("Login failed before custom post")
                return False

            ok = self.linkedin.post_to_linkedin(
                processed_text,
                image_paths=images_to_post,
                schedule_date=schedule_date,
                schedule_time=schedule_time,
            )
            logging.info(
                "Successfully posted custom text"
                if ok
                else "Failed to post custom text"
            )
            return ok

        except Exception:
            logging.error("An error occurred in post_custom_text.", exc_info=True)
            return False

    def _apply_anchor_mentions(
        self, post_text: str, anchors: Optional[List[str]], names: Optional[List[str]]
    ) -> str:
        """Inject ``@{Name}`` tokens after configured anchor phrases.

        Why:
            Allow users to specify where mentions belong without manually
            crafting placeholders.

        When:
            Called before composing text if `mention_anchors` and
            `mention_names` are provided.

        How:
            Iterates through provided anchor/name pairs, constructs regex
            patterns that respect word boundaries, and substitutes the first
            occurrence with an embedded ``@{name}`` token.

        Args:
            post_text (str): Original content.
            anchors (list[str] | None): Anchor phrases preceding a mention.
            names (list[str] | None): Corresponding display names.

        Returns:
            str: Post text with inline mention placeholders applied.
        """
        try:
            if not anchors or not names or len(anchors) != len(names):
                return post_text

            result = post_text
            for anchor, name in zip(anchors, names):
                if not anchor or not name:
                    continue
                words = str(anchor).strip().split()
                if not words:
                    continue

                pattern = r"\b" + r"\s+".join(map(re.escape, words)) + r"\b"
                replacement = r"\g<0> @{" + name + r"}"

                try:
                    result, n = re.subn(
                        pattern, replacement, result, count=1, flags=re.IGNORECASE
                    )
                    if n == 0:
                        logging.info(f"Anchor not found: '{anchor}'")
                except Exception as re_err:
                    logging.info(f"Anchor substitution failed for '{anchor}': {re_err}")
            return result
        except Exception as e:
            logging.info(f"_apply_anchor_mentions failed; returning original text: {e}")
            return post_text

    def _select_images(self, image_directory: Optional[str]) -> List[str]:
        """Pick up to three random images from a directory.

        Why:
            Avoid repetitive manual selection while still adding media variety to
            posts sourced from topic files.

        When:
            Used when the caller supplies an image directory but no explicit
            paths.

        How:
            Validates the directory, filters supported extensions, and samples
            up to three unique files.

        Args:
            image_directory (str | None): Directory path to scan for images.

        Returns:
            list[str]: Absolute file paths suitable for Selenium uploads.
        """
        if not image_directory:
            return []

        try:
            image_dir = Path(image_directory)
            if not image_dir.exists() or not image_dir.is_dir():
                logging.warning(f"Image directory does not exist: {image_directory}")
                return []

            image_files = [
                str(f)
                for f in image_dir.glob("*")
                if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif")
            ]

            if image_files:
                return random.sample(image_files, min(3, len(image_files)))

            logging.info("No images found in directory")
            return []
        except Exception as e:
            logging.error(f"Error selecting images: {e}")
            return []

    def _update_topics_file(
        self, file_path: str, topics: List[str], posted_topic: str
    ) -> None:
        """Persist topic progress by removing the used idea and logging history.

        Why:
            Prevents reposting the same topic and keeps an audit trail of what
            went live and when.

        When:
            Invoked after a successful post originating from a topics file.

        How:
            Removes the chosen topic from the in-memory list, rewrites the file
            with remaining entries, and appends a timestamped record to a
            `<topics>_posted` companion file.

        Args:
            file_path (str): Original topics file path.
            topics (list[str]): Remaining topics.
            posted_topic (str): Topic that was just published.

        Returns:
            None
        """
        try:
            topics.remove(posted_topic)
            path = Path(file_path)
            path.write_text(
                "\n".join(topics) + ("\n" if topics else ""), encoding="utf-8"
            )
            logging.info(f"Updated topics file. {len(topics)} topics remaining.")

            stem = path.stem or "topics"
            suffix = path.suffix or ".txt"
            history_path = path.with_name(f"{stem}_posted{suffix}")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with history_path.open("a", encoding="utf-8") as history_file:
                history_file.write(f"{timestamp} | {posted_topic}\n")
            logging.info("Recorded posted topic in %s", history_path)
        except ValueError:
            logging.warning(
                "Posted topic '%s' not found in %s", posted_topic, file_path
            )
        except Exception as e:
            logging.error(f"Error updating topics file: {e}")

    def close(self) -> None:
        """Terminate the Selenium session and release resources.

        Why:
            Avoid lingering browser processes and free OS resources once work is
            complete.

        When:
            Call after finishing posting or engagement workflows.

        How:
            Invokes :meth:`webdriver.Chrome.quit` and logs the outcome.

        Returns:
            None
        """
        if not self.driver:
            return
        drv = self.driver
        self.driver = None
        try:
            drv.quit()
            logging.info("Driver session ended cleanly.")
        except Exception as e:
            logging.error(f"Error closing driver: {e}")

    def _driver_window_alive(self) -> bool:
        """True when the WebDriver session still has a usable top-level window."""
        if not getattr(self, "driver", None):
            return False
        try:
            self.driver.current_window_handle
            return True
        except Exception:
            return False

    def engage_feed(
        self, action: str = "both", max_actions: int = 10
    ) -> Dict[str, Any]:
        """Perform engagement actions on the main feed.

        Args:
            action (str): Type of engagement ('like', 'comment', 'both')
            max_actions (int): Maximum number of posts to engage with

        Returns:
            Dict containing engagement stats
        """
        logging.info(f"Starting feed engagement (action={action}, max={max_actions})")

        if not getattr(self, "_login_succeeded", True):
            logging.error("Skipping feed engagement: login failed earlier in this run.")
            return {
                "success": False,
                "action": action,
                "max_actions": max_actions,
                "error": "login_failed",
            }
        if not self._driver_window_alive():
            logging.error(
                "Skipping feed engagement: no browser window (closed manually, crashed, "
                "or session lost). Keep the Chrome window open for the whole run and "
                "avoid starting a second bot while this one is active."
            )
            return {
                "success": False,
                "action": action,
                "max_actions": max_actions,
                "error": "browser_window_closed",
            }

        # Determine perspectives if commenting
        perspectives = None
        if action in ["comment", "both"]:
            perspectives = ["funny", "motivational", "insightful"]

        try:
            success = self.linkedin.engage_stream(
                mode=action,
                comment_text=config.LINKEDIN_COMMENT_FALLBACK,
                max_actions=max_actions,
                include_promoted=False,
                ai_client=self.openai_client,
                post_extractor=self.post_extractor,
                ai_perspectives=perspectives,
                ai_max_tokens=150,
                ai_temperature=0.7,
            )
            return {"success": success, "action": action, "max_actions": max_actions}
        except Exception as e:
            logging.error(f"Feed engagement failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action,
                "max_actions": max_actions,
            }

    def pursue_investor(
        self,
        profile_name: str,
        max_posts: int = 5,
        should_follow: bool = True,
        should_like: bool = True,
        should_comment: bool = True,
        comment_perspectives: Optional[List[str]] = None,
        bio_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Pursue and engage with a specific person's profile.

        Args:
            profile_name: Name of the person to engage with
            max_posts: Maximum number of posts to engage with
            should_follow: Whether to follow the profile
            should_like: Whether to like posts
            should_comment: Whether to comment on posts
            comment_perspectives: List of perspectives for AI comments

        Returns:
            Dict containing results and any errors
        """
        results = {
            "profile": profile_name,
            "followed": False,
            "posts_engaged": 0,
            "likes_given": 0,
            "comments_made": 0,
            "errors": [],
        }

        try:
            # Search for the profile with bio keywords
            logging.info(f"Searching for profile: {profile_name}")
            if bio_keywords:
                logging.info(f"Looking for bio containing: {', '.join(bio_keywords)}")

            profile_url = self.linkedin.search_profile(
                profile_name, bio_keywords=bio_keywords
            )

            if not profile_url:
                raise ValueError(f"Could not find matching profile for {profile_name}")

            # Navigate to profile
            logging.info(f"Navigating to profile: {profile_url}")
            self.linkedin.driver.get(profile_url)
            time.sleep(3)  # Wait for profile to load

            # Follow the profile if requested
            if should_follow:
                try:
                    if self.linkedin.follow_profile():
                        results["followed"] = True
                        logging.info(f"Successfully followed {profile_name}")
                except Exception as e:
                    error_msg = f"Failed to follow profile: {str(e)}"
                    results["errors"].append(error_msg)
                    logging.error(error_msg)

            # Engage directly on the profile's posts page
            logging.info(
                f"Opening profile posts view and engaging up to {max_posts} posts"
            )
            if not self.linkedin.open_profile_posts_view():
                logging.warning(
                    "Could not confirm profile posts view; continuing with current page"
                )

            comment_generator = None
            if should_comment:

                def build_comment(post_root):  # type: ignore[return-type]
                    base_text = config.LINKEDIN_COMMENT_FALLBACK
                    if self.openai_client:
                        try:
                            post_text = self.post_extractor.extract_text(post_root)
                        except Exception:
                            post_text = ""
                        if post_text:
                            try:
                                perspective = self._get_random_perspective(
                                    comment_perspectives
                                    or ["insightful", "motivational", "funny"]
                                )
                                return self.openai_client.generate_comment(
                                    post_text=post_text,
                                    perspective=perspective,
                                    max_tokens=180,
                                    temperature=0.7,
                                )
                            except Exception as err:
                                logging.error(f"AI comment generation failed: {err}")
                    return base_text

                comment_generator = build_comment

            engagement = self.linkedin.engage_profile_posts(
                max_posts=max_posts,
                should_like=should_like,
                should_comment=should_comment,
                comment_generator=comment_generator,
                mention_author=False,
                mention_position="append",
            )

            results["posts_engaged"] = engagement.get("posts_engaged", 0)
            results["likes_given"] = engagement.get("likes", 0)
            results["comments_made"] = engagement.get("comments", 0)
            if engagement.get("errors"):
                results["errors"].extend(engagement["errors"])
            logging.info(
                "Profile engagement summary: posts=%s likes=%s comments=%s skipped=%s",
                results["posts_engaged"],
                results["likes_given"],
                results["comments_made"],
                engagement.get("skipped", 0),
            )

            return results

        except Exception as e:
            error_msg = f"Error pursuing investor {profile_name}: {str(e)}"
            results["errors"].append(error_msg)
            logging.error(error_msg, exc_info=True)
            return results

    def connect_with_people(
        self,
        query: str,
        max_connects: int = 10,
        note: Optional[str] = None,
        bio_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search people by keyword and send connection requests."""
        results: Dict[str, Any] = {
            "query": query,
            "sent": 0,
            "skipped": 0,
            "errors": [],
            "success": False,
        }

        try:
            logging.info("Connecting with people matching: %s", query)
            if bio_keywords:
                logging.info(
                    "Filtering results for bio keywords: %s",
                    ", ".join(bio_keywords),
                )

            connect_results = self.linkedin.connect_people(
                query=query,
                max_connects=max_connects,
                note=note,
                bio_keywords=bio_keywords,
            )
            results.update(connect_results)
            results["success"] = results["sent"] > 0
            logging.info(
                "Connect summary: sent=%s skipped=%s errors=%s",
                results["sent"],
                results["skipped"],
                len(results["errors"]),
            )
            return results

        except Exception as e:
            error_msg = f"Error connecting with people for {query}: {str(e)}"
            results["errors"].append(error_msg)
            logging.error(error_msg, exc_info=True)
            return results

    def scan_opportunities(
        self,
        max_posts: int = 50,
        keywords: Optional[List[str]] = None,
        output_file: str = "opportunities.json",
        require_contact: bool = False,
    ) -> Dict[str, Any]:
        """Scan the home feed for job/intern posts with apply emails or forms."""
        results: Dict[str, Any] = {
            "posts_scanned": 0,
            "found": 0,
            "opportunities": [],
            "output_file": output_file,
            "errors": [],
            "success": False,
        }

        try:
            if not self._login_succeeded:
                results["errors"].append("LinkedIn login failed")
                return results

            logging.info(
                "Scanning feed for opportunities (max_posts=%s)", max_posts
            )
            if keywords:
                logging.info("Extra keywords: %s", ", ".join(keywords))

            scan = self.linkedin.scan_feed_opportunities(
                max_posts=max_posts,
                keywords=keywords,
                output_file=output_file,
                post_extractor=self.post_extractor,
                require_contact=require_contact,
            )
            results.update(scan)
            results["success"] = not results.get("errors")
            logging.info(
                "Opportunity scan summary: scanned=%s found=%s file=%s",
                results.get("posts_scanned", 0),
                results.get("found", 0),
                output_file,
            )
            return results

        except Exception as e:
            error_msg = f"Error scanning feed for opportunities: {str(e)}"
            results["errors"].append(error_msg)
            logging.error(error_msg, exc_info=True)
            return results
