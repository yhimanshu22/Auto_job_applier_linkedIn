#!/usr/bin/env python3
"""LinkedIn automation package CLI entry point.

Run via ``python -m linkedin_automation <action> [...]`` from a directory where
``linkedin_automation`` is importable (typically the backend root). Mirrors the
original standalone ``main.py``: dispatches to post / engage / pursue /
generate-calendar commands, returns a process exit code.

Heavy imports (``LinkedInBot`` and its Selenium / Gemini / OpenAI dependency
chain) are deferred to inside ``main()``, so ``python -m linkedin_automation
--help`` returns instantly instead of paying ~5s of imports.
"""

import sys
import logging
import json

from .linkedin_ui.arg_parser import setup_argument_parser

# ``config`` and ``LinkedInBot`` are imported inside :func:`main` (after
# ``parser.parse_args``) so ``--help`` and argument errors exit before paying
# the cost of pulling in Selenium / undetected-chromedriver / openai / etc.

# Commands that don't need a browser session — they only call AI helpers.
_BROWSER_FREE_COMMANDS = frozenset({"generate-calendar"})


def setup_logging(debug: bool = False) -> None:
    """Configure logging based on debug flag."""
    import os

    level = logging.DEBUG if debug else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    task_log = os.getenv("LINKDAPPLY_AUTOMATION_LOG", "").strip()
    if task_log:
        handlers.append(logging.FileHandler(task_log, mode="a", encoding="utf-8"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,
    )


def main() -> int:
    """Main entry point for the LinkedIn bot."""
    try:
        parser = setup_argument_parser()
        args = parser.parse_args()

        setup_logging(debug=args.debug)

        # Deferred: only paid once we know what command to run.
        from . import config
        from .linkedin_bot import LinkedInBot

        requires_browser = args.command not in _BROWSER_FREE_COMMANDS
        bot = LinkedInBot(
            use_openai=not args.no_ai,
            requires_browser=requires_browser,
        )
        if args.headless:
            config.HEADLESS = True

        exit_code = 0

        if args.command == "post":
            if args.post_text:
                bot.post_custom_text(
                    post_text=args.post_text,
                    image_directory=args.images_dir,
                    schedule_date=args.schedule_date,
                    schedule_time=args.schedule_time,
                )
            else:
                bot.process_topics(
                    args.topics_file,
                    image_directory=None if args.no_images else args.images_dir,
                    schedule_date=args.schedule_date,
                    schedule_time=args.schedule_time,
                )

        elif args.command == "generate-calendar":
            bot.generate_content_calendar(
                args.niche, output_file=args.output, total_posts=args.total_posts
            )

        elif args.command == "engage":
            results = bot.engage_feed(action=args.action, max_actions=args.max_actions)
            logging.info(f"Engagement results: {json.dumps(results, indent=2)}")
            if not results.get("success", True):
                exit_code = 1
                err = results.get("error") or results
                logging.error("Engage finished unsuccessfully: %s", err)

        elif args.command == "pursue":
            results = bot.pursue_investor(
                profile_name=args.profile_name,
                max_posts=args.max_posts,
                should_follow=args.should_follow,
                should_like=args.should_like,
                should_comment=args.should_comment,
                comment_perspectives=args.perspectives,
                bio_keywords=args.bio_keywords,
            )
            logging.info(f"Pursuit results: {json.dumps(results, indent=2)}")
            exit_code = 0 if not results.get("errors") else 1

        bot.close()
        if exit_code:
            logging.info("LinkedIn Bot finished with exit code %s", exit_code)
        else:
            logging.info("LinkedIn Bot completed successfully")
        return exit_code

    except Exception as e:
        logging.error(f"LinkedIn Bot encountered an error: {str(e)}", exc_info=True)
        return 1
    finally:
        if "bot" in locals():
            try:
                bot.close()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
