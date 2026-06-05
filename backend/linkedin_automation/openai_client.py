"""LLM helpers for LinkedIn post, comment, and calendar generation.

Supports OpenAI, Google Gemini, xAI Grok, and Groq (OpenAI-compatible APIs),
selected via ``LINKEDIN_AI_PROVIDER`` / available API keys in ``config``.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Literal, Optional

from . import config
from .text_utils import preprocess_for_ai


@dataclass
class ContentCalendarRequest:
    """Structured payload describing a desired LinkedIn content calendar.

    Why:
        Prompts benefit from explicit field separation, and dataclasses provide
        validation-friendly containers.

    When:
        Constructed by CLI handlers before calling
        :meth:`OpenAIClient.generate_content_calendar`.

    How:
        Stores descriptive metadata such as niche, goal, audience, tone, and
        optional inspiration fields used to craft the AI prompt.
    """

    niche: str
    goal: str
    audience: str
    tone: str
    content_types: List[str]
    frequency: str
    total_posts: int
    hashtags: List[str]
    inspiration: Optional[str] = None
    personal_story: Optional[str] = None


class OpenAIClient:
    """Multi-provider LLM client (OpenAI, Gemini, Grok, Groq) for LinkedIn copy.

    Instantiated by :class:`LinkedInBot` when :func:`config.has_linkedin_llm_credentials`
    is true. OpenAI-compatible hosts use the ``openai`` Python package; Gemini
    uses ``google.generativeai``.
    """

    def __init__(self, model: Optional[str] = None) -> None:
        self.provider = config.resolve_linkedin_ai_provider()
        self.client = None
        self.model = ""

        from openai import OpenAI

        if self.provider == "openai":
            self.model = model or config.OPENAI_MODEL
            if config.OPENAI_API_KEY:
                self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        elif self.provider == "grok":
            self.model = model or config.GROK_MODEL
            if config.GROK_API_KEY:
                self.client = OpenAI(
                    api_key=config.GROK_API_KEY,
                    base_url=config.GROK_API_BASE,
                )
        elif self.provider == "groq":
            self.model = model or config.GROQ_MODEL
            gk = config.effective_groq_api_key()
            if gk:
                self.client = OpenAI(
                    api_key=gk,
                    base_url=config.GROQ_API_BASE,
                )
        elif self.provider == "gemini":
            self.model = model or config.LINKEDIN_GEMINI_MODEL

        try:
            logging.info(
                "LinkedIn LLM: provider=%s model=%s client_ready=%s",
                self.provider,
                self.model,
                bool(self.client) or self.provider == "gemini",
            )
        except Exception:
            pass

        self.style_templates: dict[str, str] = {
            "professional": "Write with clarity, authority, and professionalism.",
            "storytelling": "Start with a short, engaging story or anecdote before the main lesson.",
            "listicle": "Present the content as 3–5 quick, punchy lessons or tips.",
            "contrarian": "Open with a bold or controversial opinion, then explain why.",
            "funny": "Use light humor, analogies, or playful tone to explain the idea.",
            "inspirational": "Be motivational and uplifting, focusing on big-picture impact."
        }

    def _llm_ready(self) -> bool:
        if self.provider == "gemini":
            return bool(config.GEMINI_API_KEY)
        return self.client is not None

    def _missing_credentials_message(self) -> str:
        return (
            f"AI not configured for provider {self.provider!r}. Set one of: "
            "OPENAI_API_KEY, GEMINI_API_KEY, GROK_API_KEY, GROQ_API_KEY / LLM_API_KEY "
            "(with LLM_API_URL for Groq), or LINKEDIN_AI_PROVIDER to pick a backend."
        )

    def _complete_chat(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        temperature: float,
        top_p: float = 0.9,
        frequency_penalty: float = 0.2,
        presence_penalty: float = 0.2,
    ) -> str:
        if self.provider == "gemini":
            return self._gemini_generate(system, user, max_tokens, temperature)
        if not self.client:
            raise ValueError(self._missing_credentials_message())
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=min(max(temperature, 0.1), 1.0),
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
        msg = response.choices[0].message
        return (getattr(msg, "content", None) or "").strip()

    def _gemini_generate(
        self, system: str, user: str, max_tokens: int, temperature: float
    ) -> str:
        if not config.GEMINI_API_KEY:
            raise ValueError(self._missing_credentials_message())
        import google.generativeai as genai

        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(self.model)
        combined = f"{system}\n\n{user}" if system.strip() else user
        gc = genai.types.GenerationConfig(
            max_output_tokens=max(1, min(max_tokens, 8192)),
            temperature=min(max(temperature, 0.0), 2.0),
        )
        resp = model.generate_content(combined, generation_config=gc)
        if not resp.candidates:
            raise ValueError("Gemini returned no candidates (blocked or empty).")
        text = (getattr(resp, "text", None) or "").strip()
        if not text:
            raise ValueError("Gemini returned empty text.")
        return text

    def _strip_disallowed_github_urls(self, text: str) -> str:
        """Remove any github.com links except this account (and its repos)."""
        if not isinstance(text, str) or not text.strip():
            return text
        user = re.escape(config.LINKEDIN_GITHUB_USERNAME)
        pattern = re.compile(rf"https?://github\.com/(?!{user}(?:/|$))[^\s)\]\"']+", re.I)
        cleaned = pattern.sub("", text)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        return cleaned

    def _append_marketing_tail(self, text: str) -> str:
        """Append a promotional tail encouraging readers to explore the project.

        Args:
            text (str): Generated OpenAI text (post, comment, or fallback).

        Returns:
            str: Text with a promotional tail when marketing mode is enabled.
        """
        if not isinstance(text, str):
            return text
        if not text or not config.MARKETING_MODE:
            return text.strip()
        if config.PROJECT_URL in text:
            return text.strip()
        tail = f"PS: Check out {config.PROJECT_NAME} – {config.PROJECT_SHORT_PITCH} {config.PROJECT_URL}"
        return f"{text.strip()} {tail}".strip()

    def generate_post(
        self,
        topic: str,
        style: str = "professional",
        max_tokens: int = 600,
        temperature: float = 0.7,
        summarize_input: bool = True
    ) -> str:
        """Produce a LinkedIn post in Joseph's voice using OpenAI.

        Why:
            Provide high-quality, structured posts tailored to the user's brand.

        When:
            Called when automated topic runs prefer OpenAI over Gemini or local
            templates.

        How:
            Optionally summarises long topics, selects a style template, crafts a
            structured prompt, and requests a chat completion.

        Args:
            topic (str): Subject matter to cover.
            style (str): Style template key controlling prompt flavour.
            max_tokens (int): Token ceiling for the generated response.
            temperature (float): Randomness setting for the completion.
            summarize_input (bool): Whether to normalise lengthy topics first.

        Returns:
            str: Generated LinkedIn post content.

        Raises:
            ValueError: If the OpenAI client is not initialised.
            Exception: Propagates API errors for upstream handling.
        """
        if not self._llm_ready():
            raise ValueError(self._missing_credentials_message())

        if summarize_input and len(topic) > 200:
            topic = preprocess_for_ai(topic, summarize_ratio=0.3, max_chars=200)

        style_instruction = self.style_templates.get(style, self.style_templates["professional"])

        PROMPT_TEMPLATE = """
You are Joseph Edomobi (joeygoesgrey), a Nigerian full-stack developer and entrepreneur.
Write a LinkedIn post about "{topic}" in a {style} style.

Project context you should weave in naturally:
{project_context}

Follow this structure:
1. **Hook** → A bold, curiosity-driven first line (e.g., "How I...", "How to... without...", "Imagine if...").
2. **Story** → Use a mini-story or analogy. Show a problem → journey → resolution.
3. **Lesson** → Share the insight or key takeaway in simple, clear language.
4. **Engagement Question** → End with a contextual question (not generic).
5. **Hashtags** → Add 3–5 strong, relevant hashtags.
6. **Image Suggestion** → Recommend what kind of image fits the post (before/after, selfie, infographic, etc.).

Rules:
- Write at a 6th–7th grade reading level.
- Short sentences. No jargon.
- Conversational tone. Sound human, not corporate.
- Keep it under 300 words.
- Do not use emojis unless natural.
- Hashtags should not be generic like #JoinTheRevolution. Prefer niche tags (e.g., #AIinHealthcare).
- Include a friendly CTA inviting readers to explore {project_name}, the open-source toolkit that {project_pitch}. Add the link {project_url} near the end without sounding spammy.

{style_instruction}
"""
        prompt = PROMPT_TEMPLATE.format(
            topic=topic,
            style=style,
            style_instruction=style_instruction,
            project_name=config.PROJECT_NAME,
            project_pitch=config.PROJECT_PITCH,
            project_url=config.PROJECT_URL,
            project_context=config.PROJECT_CONTEXT,
        )

        try:
            generated = self._complete_chat(
                system="You are a LinkedIn growth strategist who writes engaging, human-like posts.",
                user=prompt,
                max_tokens=min(max_tokens, 1000),
                temperature=min(temperature, 0.9),
                frequency_penalty=0.3,
                presence_penalty=0.3,
            )
            return self._append_marketing_tail(generated)
        except Exception as e:
            logging.error(f"Error generating post with LLM ({self.provider}): {str(e)}")
            raise

    def generate_comment(
        self,
        post_text: str,
        perspective: Literal["funny", "motivational", "insightful"],
        max_tokens: int = 150,
        temperature: float = 0.7,
        summarize_input: bool = True
    ) -> str:
        """Draft a conversational LinkedIn comment from a given perspective.

        Why:
            Engagement loops need authentic-sounding replies tailored to the
            post's tone.

        When:
            Called by the engage stream whenever AI commenting is enabled.

        How:
            Optionally summarises long posts, selects a perspective-specific
            instruction, and requests a concise chat completion.

        Args:
            post_text (str): Source post content.
            perspective (Literal["funny", "motivational", "insightful"]): Desired
                tone for the reply.
            max_tokens (int): Token cap for the response.
            temperature (float): Sampling temperature passed to OpenAI.
            summarize_input (bool): Whether to trim long source posts.

        Returns:
            str: Generated comment, or a fallback message when errors occur.

        Raises:
            ValueError: If the OpenAI client is missing.
        """
        if not self._llm_ready():
            raise ValueError(self._missing_credentials_message())

        perspective_map: dict[str, str] = {
            "funny": "Light wit or a dry aside that fits the post — still professional.",
            "motivational": "Warm, specific encouragement tied to what they actually said.",
            "insightful": "One concrete observation, question, or experience that extends their point.",
        }

        processed_text = post_text
        if summarize_input and len(post_text) > 300:
            processed_text = preprocess_for_ai(
                post_text,
                summarize_ratio=0.3,
                max_chars=300
            )

        resume_block = (
            f"You may offer your resume only when it genuinely fits (e.g. hiring, referrals, "
            f"resume feedback, job search, interviews). If you mention it, use exactly this link: {config.LINKEDIN_RESUME_URL}. "
            "If it does not fit, do not mention a resume."
            if config.LINKEDIN_RESUME_URL
            else "Do not mention a resume or portfolio file unless the post explicitly asks for one (then say you can share it in a DM without inventing links)."
        )

        cfbr_block = (
            "Optional last line: you may add CFBR alone (nothing else on that line) when the post is light, "
            "celebratory, tips, hiring shout-outs, or generic professional wins — never on setbacks.\n"
            if config.LINKEDIN_COMMENT_CFBR
            else ""
        )

        project_cta_block = (
            f"After your reply, add one short line inviting readers to explore {config.PROJECT_NAME} — "
            f"{config.PROJECT_SHORT_PITCH} — only this link: {config.PROJECT_URL}. Under ~20 words.\n"
            if config.LINKEDIN_COMMENT_APPEND_PROJECT_CTA
            else "Do not promote any product, repo, newsletter, or 'LinkedIn bot' / automation toolkit. No PS lines.\n"
        )

        COMMENT_PROMPT_TEMPLATE = """Write ONE LinkedIn comment as {who}.

Post content:
{post_text}

Tone and safety (critical):
- Read the emotional context. If the post is about a revoked or rescinded offer, layoffs, rejection, job loss, grief, serious illness, legal trouble, discrimination, burnout, or similar — respond with brief empathy, solidarity, or a thoughtful question. Never use celebratory praise, "Thanks for sharing", "Great post", "love this", or upbeat corporate cheer — that reads as tone-deaf and inauthentic.
- If they are venting or hurting, acknowledge that; do not pivot to self-promotion or jokes.

Hard rules:
- {voice}
- Tone angle: {perspective_instruction} — but defer to the tone-and-safety rules above when they conflict.
- First person; sound like a human who read the post, not a bot or growth hack.
- 1–3 short sentences max (CFBR line counts as its own line if used). No bullet lists, no emojis, no quotation marks around the whole comment.
- React to something specific in the post — not generic praise.
- GitHub: if you mention GitHub at all, the ONLY GitHub profile URL allowed is {allowed_github_url}. You may link repos under that profile (e.g. {allowed_github_url}/repo). Never link or name any other GitHub user or org.
- {resume_block}
- {project_cta_block}{cfbr_block}
Comment (plain text only):"""

        prompt = COMMENT_PROMPT_TEMPLATE.format(
            who=who,
            post_text=processed_text,
            voice=config.LINKEDIN_COMMENT_VOICE,
            perspective_instruction=perspective_map[perspective],
            allowed_github_url=config.LINKEDIN_GITHUB_URL,
            resume_block=resume_block,
            project_cta_block=project_cta_block,
            cfbr_block=cfbr_block,
        )

        system = (
            f"You write LinkedIn comments as {who}. "
            "You never fabricate links. You follow the user's GitHub and resume rules exactly."
        )

        try:
            comment = self._complete_chat(
                system=system,
                user=prompt,
                max_tokens=min(max(max_tokens, 20), 300),
                temperature=min(max(temperature, 0.1), 1.0),
                frequency_penalty=0.2,
                presence_penalty=0.2,
            )
            comment = comment.strip('"\'').strip()

            if comment:
                if config.LINKEDIN_COMMENT_APPEND_PROJECT_CTA:
                    comment = self._append_marketing_tail(comment)
            else:
                comment = config.LINKEDIN_COMMENT_FALLBACK

            comment = self._strip_disallowed_github_urls(comment)

            logging.info(f"Generated {perspective} comment with {len(comment)} characters")

            return comment

        except Exception as e:
            logging.error(f"Error generating comment: {e}")
            return self._strip_disallowed_github_urls(config.LINKEDIN_COMMENT_FALLBACK)

    def generate_content_calendar(self, request: ContentCalendarRequest) -> str:
        """Draft a LinkedIn content calendar based on user-supplied goals.

        Why:
            Help users plan multi-day content campaigns without manual drafting.

        When:
            Invoked by the CLI ``--generate-calendar`` workflow.

        How:
            Builds a detailed prompt describing niche, goals, tone, and optional
            inspiration, then requests a chat completion that emits day-by-day
            ideas.

        Args:
            request (ContentCalendarRequest): Structured description of the
                desired calendar.

        Returns:
            str: AI-generated calendar text.

        Raises:
            ValueError: If the OpenAI client is not initialised.
            Exception: Propagates API errors for caller handling.
        """

        if not self._llm_ready():
            raise ValueError(self._missing_credentials_message())

        content_types = ", ".join(request.content_types) if request.content_types else "a variety of formats"
        hashtags = ", ".join(f"#{tag.lstrip('#')}" for tag in request.hashtags) if request.hashtags else "relevant hashtags"
        inspiration = request.inspiration or ""
        personal_story = request.personal_story or ""

        inspiration_clause = (
            f"- The user admires or draws inspiration from {inspiration}.\n" if inspiration else ""
        )
        personal_clause = (
            f"- The user wants to weave in personal stories such as: {personal_story}.\n" if personal_story else ""
        )

        prompt = f"""
I need help generating a {request.total_posts}-day content plan for the {request.niche} niche.
The user wants to focus on {request.goal} and their target audience is {request.audience}.
The content should be written in a {request.tone} tone. Posts should emphasise {content_types}.
Please follow these guidelines:
- Posting frequency: {request.frequency}
- Use these hashtags or keywords throughout: {hashtags}
{inspiration_clause}{personal_clause}
Output {request.total_posts} unique post ideas. For each idea, produce a single line in the format:
Day X | Hook | Content Description | Suggested CTA | Suggested hashtags
Hooks should be catchy, descriptions concise (one to two sentences), CTA actionable, and hashtags relevant.
Avoid duplicate ideas and keep the tone consistent with the brief.
"""

        try:
            calendar_text = self._complete_chat(
                system=(
                    "You are an expert LinkedIn content strategist who creates month-long content calendars "
                    "with concise, actionable ideas."
                ),
                user=prompt,
                max_tokens=min(max(request.total_posts * 80, 600), 3000),
                temperature=0.7,
                frequency_penalty=0.2,
                presence_penalty=0.2,
            )
            logging.info(
                "Generated content calendar with %d characters", len(calendar_text)
            )
            return calendar_text
        except Exception as exc:
            logging.error(f"Error generating content calendar: {exc}")
            raise
