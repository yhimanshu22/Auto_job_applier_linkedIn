"""Regression tests for the LinkedIn-automation package cold-start budget.

These tests guard the import laziness that ships in the package. Every
``python -m linkedin_automation ...`` subprocess pays its full import cost on
startup, so a regression here directly slows every dashboard action.

We assert two distinct things via fresh subprocesses (so the test process's
own ``sys.modules`` doesn't pollute the result):

1. **No heavy imports at module load.** Importing
   ``linkedin_automation.__main__`` must not pull Selenium /
   undetected_chromedriver / openai / google.generativeai / sumy /
   webdriver_manager into ``sys.modules``.

2. **No heavy imports for ``--help``.** Running the CLI with ``--help`` must
   short-circuit before any of the above land in ``sys.modules`` either,
   since argparse exits without instantiating ``LinkedInBot``.

3. **``LinkedInBot(requires_browser=False)`` is browser-free.** Constructing
   the bot in calendar mode must NOT import Selenium / Chrome stacks.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest


HEAVY_MODULES = [
    "selenium",
    "undetected_chromedriver",
    "openai",
    "google.generativeai",
    "sumy",
    "webdriver_manager",
]


def _backend_root() -> str:
    """Return the backend root path so subprocesses can ``-m linkedin_automation``."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_inline(code: str, args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run ``python -c <code>`` in a fresh interpreter rooted at backend/."""
    cmd = [sys.executable, "-c", code] + (args or [])
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=_backend_root(),
        timeout=60,
    )


# ---------------------------------------------------------------------------
# 1) Importing the entry-point module is heavy-free
# ---------------------------------------------------------------------------


def test_main_module_import_does_not_pull_heavy_deps():
    """Importing ``linkedin_automation.__main__`` must not load Selenium et al."""
    code = (
        "import sys\n"
        "import linkedin_automation.__main__\n"  # noqa: E501 — purposeful side effect
        "heavy = " + repr(HEAVY_MODULES) + "\n"
        "loaded = [m for m in heavy if m in sys.modules]\n"
        "print('LOADED:', ','.join(loaded))\n"
    )
    result = _run_inline(code)
    assert result.returncode == 0, (
        f"stderr:\n{result.stderr}\nstdout:\n{result.stdout}"
    )
    line = [
        line for line in result.stdout.splitlines() if line.startswith("LOADED:")
    ]
    assert line, f"Marker missing in stdout:\n{result.stdout}"
    loaded_str = line[-1].split("LOADED:", 1)[1].strip()
    loaded = [m for m in loaded_str.split(",") if m]
    assert not loaded, f"Heavy modules eagerly imported: {loaded}"


# ---------------------------------------------------------------------------
# 2) ``python -m linkedin_automation --help`` is heavy-free
# ---------------------------------------------------------------------------


def test_help_invocation_does_not_pull_heavy_deps():
    """The CLI ``--help`` path exits before instantiating ``LinkedInBot``.

    We patch ``builtins.print`` and the argparse exit hook to capture the
    state of ``sys.modules`` after parsing, before SystemExit fires.
    """
    code = (
        "import sys\n"
        "sys.argv = ['linkedin_automation', '--help']\n"
        "import io\n"
        "old_stdout = sys.stdout\n"
        "sys.stdout = io.StringIO()\n"
        "try:\n"
        "    from linkedin_automation.__main__ import main\n"
        "    main()\n"
        "except SystemExit:\n"
        "    pass\n"
        "sys.stdout = old_stdout\n"
        "heavy = " + repr(HEAVY_MODULES) + "\n"
        "loaded = [m for m in heavy if m in sys.modules]\n"
        "print('LOADED:', ','.join(loaded))\n"
    )
    result = _run_inline(code)
    assert result.returncode == 0, result.stderr
    line = [
        line for line in result.stdout.splitlines() if line.startswith("LOADED:")
    ][-1]
    loaded = [m for m in line.split("LOADED:", 1)[1].strip().split(",") if m]
    assert not loaded, f"Heavy modules pulled during --help: {loaded}"


# ---------------------------------------------------------------------------
# 3) Browser-free ``LinkedInBot`` does not pull Selenium
# ---------------------------------------------------------------------------


def test_browser_free_linkedin_bot_skips_selenium():
    """``LinkedInBot(requires_browser=False)`` must not import Selenium stacks."""
    code = (
        "import sys\n"
        "from linkedin_automation.linkedin_bot import LinkedInBot\n"
        "bot = LinkedInBot(use_openai=False, requires_browser=False)\n"
        "browser_only = ['selenium', 'undetected_chromedriver', 'webdriver_manager']\n"
        "loaded = [m for m in browser_only if m in sys.modules]\n"
        "print('LOADED:', ','.join(loaded))\n"
        "print('DRIVER_IS_NONE:', bot.driver is None)\n"
        "print('LINKEDIN_IS_NONE:', bot.linkedin is None)\n"
        "bot.close()\n"
        "print('CLOSE_OK')\n"
    )
    result = _run_inline(code)
    assert result.returncode == 0, (
        f"stderr:\n{result.stderr}\nstdout:\n{result.stdout}"
    )
    out = result.stdout
    loaded_line = [line for line in out.splitlines() if line.startswith("LOADED:")][-1]
    loaded = [m for m in loaded_line.split("LOADED:", 1)[1].strip().split(",") if m]
    assert not loaded, f"Browser-only modules pulled in calendar mode: {loaded}"
    assert "DRIVER_IS_NONE: True" in out
    assert "LINKEDIN_IS_NONE: True" in out
    assert "CLOSE_OK" in out


def test_browser_free_linkedin_bot_still_has_content_generator():
    """``ContentGenerator`` is needed for ``generate-calendar``; keep it eager
    inside ``__init__`` (but without dragging Gemini at module load time)."""
    code = (
        "import sys\n"
        "from linkedin_automation.linkedin_bot import LinkedInBot\n"
        "bot = LinkedInBot(use_openai=False, requires_browser=False)\n"
        "print('CG:', bot.content_generator is not None)\n"
        "print('CG_TYPE:', type(bot.content_generator).__name__)\n"
    )
    result = _run_inline(code)
    assert result.returncode == 0, result.stderr
    assert "CG: True" in result.stdout
    assert "CG_TYPE: ContentGenerator" in result.stdout


# ---------------------------------------------------------------------------
# 4) Service-level command building still passes through ``__main__`` cleanly
# ---------------------------------------------------------------------------


def test_help_subprocess_exit_code_zero():
    """End-to-end smoke: the actual subprocess used by the dashboard route."""
    result = subprocess.run(
        [sys.executable, "-m", "linkedin_automation", "--help"],
        capture_output=True,
        text=True,
        cwd=_backend_root(),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "post" in result.stdout
    assert "generate-calendar" in result.stdout


# ---------------------------------------------------------------------------
# 5) The lazy ``linkedin_ui.__getattr__`` shim still works
# ---------------------------------------------------------------------------


def test_lazy_linkedin_interaction_still_importable():
    """``from linkedin_automation.linkedin_ui import LinkedInInteraction`` must
    keep working even though the package-level attribute is now lazy."""
    code = (
        "from linkedin_automation.linkedin_ui import LinkedInInteraction\n"
        "print('CLASS:', LinkedInInteraction.__name__)\n"
    )
    result = _run_inline(code)
    assert result.returncode == 0, result.stderr
    assert "CLASS: LinkedInInteraction" in result.stdout


def test_unknown_attribute_on_linkedin_ui_raises():
    """The PEP 562 ``__getattr__`` must still raise for unknown names."""
    code = (
        "import linkedin_automation.linkedin_ui as ui\n"
        "try:\n"
        "    ui.NotAClass\n"
        "    print('NO_ERROR')\n"
        "except AttributeError as e:\n"
        "    print('ATTR_ERROR:', e)\n"
    )
    result = _run_inline(code)
    assert result.returncode == 0, result.stderr
    assert "ATTR_ERROR" in result.stdout
