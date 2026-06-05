# LinkedIn Bot – Clicks The Platform So You Don’t Have To

This Python project opens a real Chromium/Chrome browser, signs into LinkedIn, and performs everyday actions for you—posting, scheduling, uploading images, tagging people, liking, commenting, and running an AI-powered engagement loop. Everything is driven from the command line; no hidden APIs, no browser extensions: the bot simply automates the official web UI with Selenium.

## Table of Contents
- [1. Quick Start](#1-quick-start)
- [2. Features At A Glance](#2-features-at-a-glance)
- [3. Install & Configure](#3-install--configure)
- [4. Common Workflows](#4-common-workflows)
- [5. Engage Stream Safety & De-duplication](#5-engage-stream-safety--de-duplication)
- [6. AI Notes](#6-ai-notes)
  - [Bot in Action](#bot-in-action)
- [7. Configuration Reference](#7-configuration-reference)
- [8. Safety Checklist](#8-safety-checklist)
- [9. Project Structure](#9-project-structure)
- [10. Contributing](#10-contributing)
- [11. Changelog Highlights](#11-changelog-highlights)
- [12. License](#12-license)

---

## 1. Quick Start

```bash
pip install -r requirements.txt

cat <<'ENV' > .env
LINKEDIN_USERNAME=you@example.com
LINKEDIN_PASSWORD=yourLinkedInPassword
OPENAI_API_KEY=sk-your-openai-key    # optional (AI comments)
# HEADLESS=false                     # uncomment to watch the browser
ENV

python main.py --post-text "Hello LinkedIn!" --no-ai --debug --headless=false
```

Add `--headless=false` the first few runs so you can watch what’s happening. Abort with `Ctrl+C` if anything looks wrong—the browser closes automatically.

---

## 2. Features At A Glance

| Capability | What it does |
|------------|--------------|
| Post text | Publish immediately with `--post-text` (skip AI with `--no-ai`). |
| Attach images | Use `--image` (repeatable) or `--images-dir`; bot uploads via the hidden file input. |
| Schedule | Pick date/time via `--schedule-date mm/dd/yyyy` and `--schedule-time "10:45 AM"`. |
| Use/fallback AI | Use Gemini/OpenAI, your topic file, or local templates. Disable with `--no-ai`. |
| Content calendar | `--generate-calendar` creates a 30-day plan (appends to topics file; supports overwrite and defaults when optional fields are skipped). |
| Mentions | Inline `@{Ada Lovelace}`, anchor/name pairs, or auto-tag author (`--mention-author`). |
| Feed one-shots | Like/comment/repost the first visible feed item. |
| Engage stream | Scroll the feed, skip promos, like/comment repeatedly (`--engage-stream`). |
| AI summariser | Sumy condenses posts and logs the full summary before OpenAI writes a reply. |
| Human-like delays | Control pace with `--delay-min/max` and `--scroll-wait-min/max`. |
| Safety guards | Avoid duplicate comments/likes using URNs, hashes, DOM markers, and cached state. |
| **Marketing mode** | Automatically append promotional tails to AI-generated posts/comments with your project details. |

---

## 3. Install & Configure

1. **Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment variables** (create `.env`)
   ```ini
   LINKEDIN_USERNAME=you@example.com
   LINKEDIN_PASSWORD=yourLinkedInPassword
   OPENAI_API_KEY=sk-your-openai-key    # optional (AI comments)
   GEMINI_API_KEY=your_gemini_key       # optional (AI posts)
   HEADLESS=true                        # default; override per run
   USE_GEMINI=true
   
   # Marketing Mode (optional)
   MARKETING_MODE=true                  # Append promotional tails to AI content
   PROJECT_NAME=LinkedIn Bot
   PROJECT_URL=https://github.com/joeygoesgrey/linkedln-bot
   PROJECT_SHORT_PITCH=Human-like Selenium automation for LinkedIn
   ```

3. **Run with help**
   ```bash
   python main.py --help
   ```

4. **Watch the first run** (`--headless=false --debug`) to validate selectors and mention behaviour.

5. **Check logs** in `logs/linkedin_bot_YYYYMMDD_HHMMSS.log`. Useful tags: `ENGAGE_KEYS`, `ENGAGE_SKIP`, `COMMENT_ORDER`, `MENTIONS_*`, `SCROLL_*`.

---

## 4. Common Workflows

### Post plain text
```bash
python main.py post --post-text "Hello LinkedIn 👋" --no-ai --debug
```

### Post with images
```bash
python main.py post \
  --post-text "Shipping screenshots" \
  --images-dir ./static \
  --debug
```

### Schedule a post
```bash
python main.py post \
  --post-text "See you tomorrow" \
  --schedule-date 09/16/2025 \
  --schedule-time "10:45 AM"
```

### Engage with feed
```bash
python main.py engage \
  --action both \
  --max-actions 5 \
  --debug
```
- `--action`: Choose `like`, `comment`, or `both`.
- `--max-actions`: Limit the number of posts to process.

### Pursue a specific profile
```bash
python main.py pursue "Lara Acosta" \
  --max-posts 3 \
  --perspectives insightful professional \
  --bio-keywords investor venture \
  --debug
```
- Only works if you can search and view the profile's posts.
- `--perspectives`: Sets the tone for AI comments (funny, motivational, insightful).

### Generate a 30-day content calendar
```bash
python main.py generate-calendar \
  --niche "fitness" \
  --total-posts 30 \
  --output Topics.txt
```

---

## 5. Engage Stream Safety & De-duplication

- **Order**: comment first, then like.
- **De-dup cache**: URNs and text hashes persist in `logs/engage_state.json` (7-day TTL).
- **Skip logic**: checks for prior likes, existing “You” comments, and similar comment text before posting.
- **Mentions**: author mention is force-prepended when using AI.
- **Topic history**: successfully posted topics are removed from the source file and appended (with timestamps) to `<topics>_posted.<ext>`.

Troubleshooting duplicates:
1. Run headful with `--debug` and a small cap.
2. Inspect the log for `ENGAGE_SKIP reason=...` to see why a post was skipped or processed.
3. Make sure the author name appears in the feed DOM; adjust selectors in `linkedin_ui/engage_dom.py` if you notice missing names.

---

## 6. AI Notes

- **Summaries**: Sumy TextRank condenses long posts and normalises whitespace (no newlines/excess spaces) before hitting OpenAI.
- **Comments**: `openai_client.py` uses style hints; you can tweak them to allow emojis, change tone, or shorten responses.
- **Token billing**: everything you send (including spaces and line breaks) counts as tokens.
- **Fallbacks**: if OpenAI/Gemini fail, the bot falls back to `CUSTOM_POSTS_FILE` templates, then to randomised phrases.

### Bot in Action

[![LinkedIn post authored by the bot](static/linkedln%20image.png)](https://www.linkedin.com/feed/update/urn:li:share:7378393785791156224)

> Click the image to open the live LinkedIn post that was created by this automation.

![LinkedIn comment impressions generated by the bot](static/bot%20evidence.jpeg)

> The bot also drives meaningful engagement—this screenshot shows one of its comments reaching over 600 impressions.


### Documentation & Introspection

- Every module, class, and function now ships with Why/When/How docstrings so you can `help()` anything in the stack and understand intent quickly.
- Re-run the bot with `--debug` to see the enriched logging alongside the new structured docs if you are auditing behaviour.
- Export docs into plain text with:
  ```bash
  python - <<'PY'
  import inspect
  from linkedin_bot import LinkedInBot

  print(inspect.getdoc(LinkedInBot.post_custom_text))
  PY
  ```
  The output mirrors the new docstring format (What/Why/When/How, Args, Returns), making it easy to embed in your own runbooks.

---

## 7. Configuration Reference

| Location | Purpose |
|----------|---------|
| `.env` | Credentials, API keys, default headless mode, etc. |
| `config.py` | Constants (selectors, timeouts, logging format, user agent). |
| `linkedin_ui/` | Modular Selenium mixins (login, composer, mentions, engage, etc.). |
| `logs/` | Run logs + engage cache (`engage_state.json`). |
| `requirements.txt` | Python dependencies. |

Reset the engage cache by deleting `logs/engage_state.json`.

---

## 8. Safety Checklist

- Follow LinkedIn’s Terms. Use humane delays and sensible limits.
- Start with `--headless=false --debug` so you understand each step.
- Store `.env` securely. Consider a separate account for testing.
- Review logs periodically to confirm mention placement and summary output.

---

## 9. Project Structure

```
├── main.py                # CLI entry point
├── config.py              # Central configuration
├── linkedin_bot.py        # High-level orchestrator
├── linkedin_ui/
│   ├── engage.py          # Orchestrator, context builder
│   ├── engage_flow.py     # Engage loop + AI summariser/comment
│   ├── engage_dom.py      # DOM helpers (author lookup, mention support)
│   ├── engage_utils.py    # Utilities (pauses, perspectives, summariser)
│   ├── engage_types.py    # Dataclasses for engage context
│   ├── ...                # login.py, composer.py, mentions.py, etc.
├── openai_client.py       # OpenAI prompt helpers
├── content_generator.py   # Gemini/local post generation
├── logs/                  # Session logs + engage_state.json
└── static/                # Example images
```

---
## 11. Changelog Highlights

- Modularised LinkedIn UI logic under `linkedin_ui/`.
- Added AI summarisation and OpenAI comment generation with full summary logging.
- Hardened engage stream (comment-first, dedupe per URN/text hash, session cache).
- Restored mention reliability by reintroducing author extraction and caret control.
- Added CLI scheduling, explicit image attachment, and safety diagnostics (`SCROLL_*`, `ENGAGE_SKIP`).
- Expanded docstrings across the entire codebase with Why/When/How context for every module, class, and function to streamline onboarding and maintenance.

---
