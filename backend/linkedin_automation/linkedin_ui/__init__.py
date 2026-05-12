"""
LinkedIn UI package.

Why:
    Groups LinkedIn Selenium interaction logic into focused modules (login,
    overlays, composer, mentions, media, verification) to keep the codebase
    maintainable as LinkedIn’s UI evolves.

When:
    Import `LinkedInInteraction` to automate login, posting, mentions, and
    media uploads.

How:
    The `LinkedInInteraction` class composes multiple mixins that each
    encapsulate a coherent area. ``LinkedInInteraction`` itself is exposed
    via PEP 562 ``__getattr__`` so importing siblings of this package
    (``arg_parser`` for example) doesn't pull in Selenium and the engagement
    mixins. Anything that actually needs the class still gets it via
    ``from linkedin_automation.linkedin_ui import LinkedInInteraction``.
"""

__all__ = ["LinkedInInteraction"]


def __getattr__(name):
    # Lazy attribute access (PEP 562). Triggered only when callers explicitly
    # reach for ``linkedin_ui.LinkedInInteraction`` (or via ``from ... import``).
    # Submodule imports like ``linkedin_ui.arg_parser`` bypass this entirely,
    # so they no longer drag Selenium into ``sys.modules`` at startup.
    if name == "LinkedInInteraction":
        from .interaction import LinkedInInteraction

        return LinkedInInteraction
    raise AttributeError(f"module 'linkedin_automation.linkedin_ui' has no attribute {name!r}")

