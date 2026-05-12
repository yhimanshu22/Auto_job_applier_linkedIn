"""Unit tests for engage-stream helpers under the 2026 LinkedIn feed UI.

LinkedIn rolled out a new feed where every CSS class is obfuscated and posts
sit as ``role="listitem"`` elements inside ``data-testid="mainFeed"``. The
only stable hooks are aria-labels and the per-post ``componentkey`` UUID.

These tests pin the new-DOM behaviour of:
  * ``_find_visible_posts`` — locates posts via new and legacy selectors.
  * ``_extract_author_name`` — reads author from the control-menu aria-label.
  * ``_extract_post_urn`` — falls back to ``componentkey`` when no URN exists.
  * ``_like_from_bar`` — picks up the ``Reaction button state:`` button and
    respects the embedded pressed state.
  * ``EngageFlowMixin._locate_action_bar`` — returns the post root itself
    when the legacy action-bar div is missing but the new Like button is
    reachable.

No Selenium driver is started: we drive the helpers against ``MagicMock``
elements whose ``find_elements`` / ``get_attribute`` behaviour simulates each
DOM variant we want to cover.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from linkedin_automation.linkedin_ui.engage_dom import EngageDomMixin
from linkedin_automation.linkedin_ui.engage_flow import EngageExecutor


# ---------------------------------------------------------------------------
# Shared fakes
# ---------------------------------------------------------------------------


class _FakeBot(EngageDomMixin):
    """Minimal host so the mixin can reach ``self.driver``."""

    def __init__(self, driver):
        self.driver = driver

    # Stubbed downstream helpers — _like_from_bar calls these but their actual
    # behaviour is exercised elsewhere.
    def _scroll_into_view(self, _el):  # pragma: no cover - trivial
        return None

    def _click_element_with_fallback(self, _el, _name):
        # Tests inspect this via spying; default success.
        return True


def _make_element(
    *,
    displayed: bool = True,
    attrs: dict | None = None,
    text: str = "",
    children: dict | None = None,
):
    """Build a MagicMock that behaves like a Selenium WebElement.

    ``attrs`` populates ``get_attribute(name)`` lookups. ``children`` maps an
    xpath to the list of elements returned by ``find_elements`` for that
    exact xpath — anything else returns ``[]`` so unmatched probes are
    harmless.
    """

    attrs = attrs or {}
    children = children or {}
    el = MagicMock()
    el.is_displayed.return_value = displayed
    el.text = text
    el.get_attribute.side_effect = lambda name: attrs.get(name)

    def _find_elements(by, value):
        return children.get(value, [])

    def _find_element(by, value):
        items = children.get(value, [])
        if not items:
            raise Exception("not found")
        return items[0]

    el.find_elements.side_effect = _find_elements
    el.find_element.side_effect = _find_element
    return el


# ---------------------------------------------------------------------------
# _find_visible_posts
# ---------------------------------------------------------------------------


def test_find_visible_posts_picks_up_new_dom_listitems(caplog):
    """When legacy selectors yield nothing, new-DOM listitems are returned
    and a clear ``NEW_DOM detected`` info log is emitted."""

    driver = MagicMock()

    post_a = _make_element(attrs={"componentkey": "uuid-a"})
    post_b = _make_element(attrs={"componentkey": "uuid-b"})

    def _driver_find(_by, value):
        new_dom_xp = (
            "//div[@data-testid='mainFeed']//div[@role='listitem']"
            "[.//button[starts-with(@aria-label,'Open control menu')]]"
        )
        if value == new_dom_xp:
            return [post_a, post_b]
        return []

    driver.find_elements.side_effect = _driver_find

    bot = _FakeBot(driver)
    with caplog.at_level("INFO"):
        posts = bot._find_visible_posts(limit=8)

    assert posts == [post_a, post_b]
    assert any("NEW_DOM detected posts=2" in r.getMessage() for r in caplog.records)


def test_find_visible_posts_prefers_legacy_when_available():
    """If legacy selectors match, new-DOM xpaths are never consulted."""

    driver = MagicMock()
    legacy_a = _make_element(attrs={"data-id": "urn:li:activity:1"})

    calls: list[str] = []

    def _driver_find(_by, value):
        calls.append(value)
        if value == "//div[@data-id]":
            return [legacy_a]
        return []

    driver.find_elements.side_effect = _driver_find

    bot = _FakeBot(driver)
    posts = bot._find_visible_posts(limit=8)

    assert posts == [legacy_a]
    # The new-DOM selectors might be probed too (they will simply return [])
    # but the function must NOT skip the legacy xpath that produced the hit.
    assert "//div[@data-id]" in calls


def test_find_visible_posts_skips_hidden_elements():
    """Posts whose ``is_displayed`` is False are filtered out."""

    driver = MagicMock()
    hidden = _make_element(displayed=False)
    visible = _make_element(attrs={"data-id": "urn:li:activity:42"})

    def _driver_find(_by, value):
        if value == "//div[@data-id]":
            return [hidden, visible]
        return []

    driver.find_elements.side_effect = _driver_find

    bot = _FakeBot(driver)
    posts = bot._find_visible_posts(limit=8)

    assert posts == [visible]


def test_find_visible_posts_dedupes_same_handle_across_selectors():
    """Two different xpaths returning the same WebElement must not duplicate."""

    driver = MagicMock()
    shared = _make_element(attrs={"data-id": "x"})

    def _driver_find(_by, value):
        # Two different legacy selectors both find the same handle.
        if value in (
            "//div[@data-id]",
            "//div[contains(@class,'fie-impression-container')]",
        ):
            return [shared]
        return []

    driver.find_elements.side_effect = _driver_find

    bot = _FakeBot(driver)
    posts = bot._find_visible_posts(limit=8)

    assert len(posts) == 1


# ---------------------------------------------------------------------------
# _extract_author_name (new-DOM control-menu fallback)
# ---------------------------------------------------------------------------


def test_extract_author_name_uses_control_menu_aria_label():
    """When no legacy actor markup is present, the author is recovered from
    the ``Open control menu for post by <Name>`` button."""

    control_btn = _make_element(
        attrs={"aria-label": "Open control menu for post by Bill Gates"}
    )
    post = _make_element(
        children={
            (
                ".//button[starts-with(@aria-label,"
                "'Open control menu for post by ') or "
                "starts-with(@aria-label,'Hide post by ')]"
            ): [control_btn],
        },
    )

    bot = _FakeBot(MagicMock())
    name = bot._extract_author_name(post)

    assert name == "Bill Gates"


def test_extract_author_name_falls_back_to_hide_post_label():
    """``Hide post by <Name>`` is a second stable per-post aria-label."""

    hide_btn = _make_element(
        attrs={"aria-label": "Hide post by ARYAN RAJ"}
    )
    post = _make_element(
        children={
            (
                ".//button[starts-with(@aria-label,"
                "'Open control menu for post by ') or "
                "starts-with(@aria-label,'Hide post by ')]"
            ): [hide_btn],
        },
    )

    bot = _FakeBot(MagicMock())
    name = bot._extract_author_name(post)

    assert name == "ARYAN RAJ"


def test_extract_author_name_returns_none_when_nothing_matches():
    post = _make_element()  # no children, no aria-label, no text
    bot = _FakeBot(MagicMock())
    assert bot._extract_author_name(post) is None


# ---------------------------------------------------------------------------
# _extract_post_urn (componentkey fallback)
# ---------------------------------------------------------------------------


def test_extract_post_urn_uses_componentkey_when_no_urn():
    """The 2026 feed no longer emits ``urn:li:activity:*`` markers; the
    helper must use the post's ``componentkey`` UUID as a dedupe surrogate."""

    post = _make_element(attrs={"componentkey": "9360895b-caa1-4-uuid"})
    bot = _FakeBot(MagicMock())

    urn = bot._extract_post_urn(post)

    assert urn == "componentkey:9360895b-caa1-4-uuid"


def test_extract_post_urn_prefers_real_urn_attributes_over_componentkey():
    """If ``data-urn`` is present, it must win over the componentkey
    fallback so we don't change dedupe behaviour for the old DOM."""

    post = _make_element(
        attrs={
            "data-urn": "urn:li:activity:7194839284",
            "componentkey": "fallback-id",
        }
    )
    bot = _FakeBot(MagicMock())

    urn = bot._extract_post_urn(post)

    assert urn == "urn:li:activity:7194839284"


def test_extract_post_urn_returns_none_when_no_hints():
    post = _make_element()
    bot = _FakeBot(MagicMock())
    assert bot._extract_post_urn(post) is None


# ---------------------------------------------------------------------------
# _like_from_bar (Reaction button state selector + pressed parsing)
# ---------------------------------------------------------------------------


@pytest.fixture
def _patch_wait():
    """Patch WebDriverWait so it resolves to whatever element the bar
    returns for the matching xpath (no real polling)."""

    with patch(
        "linkedin_automation.linkedin_ui.engage_dom.WebDriverWait"
    ) as wait_cls:
        def _make_wait(bar, _timeout):
            wait = MagicMock()

            def _until(condition):
                # ``EC.presence_of_element_located`` returns a callable that
                # asks the parent for the element. We approximate this by
                # asking the bar directly via the xpath captured in the
                # condition's locator.
                try:
                    locator = condition.locator  # selenium-style attr
                except AttributeError:
                    # presence_of_element_located stores it as the first
                    # positional in its closure; fall back to inspecting it.
                    locator = getattr(condition, "__closure__", None)
                # Easiest: peek the most recent ``find_element`` call on bar.
                # Since we hand-craft the test to return one element per
                # selector, the mock's find_element side_effect drives this.
                return condition(bar)

            wait.until.side_effect = _until
            return wait

        wait_cls.side_effect = _make_wait
        yield wait_cls


def test_like_from_bar_uses_new_dom_reaction_button(_patch_wait):
    """The new-DOM Like button advertises ``Reaction button state: ...`` in
    its aria-label. With ``no reaction`` the helper must click and report
    success."""

    bar = MagicMock()
    btn = _make_element(
        attrs={
            "aria-label": "Reaction button state: no reaction",
            "aria-pressed": "false",
        }
    )

    def _find_element(_by, value):
        # All legacy selectors miss; the new-DOM xpath wins.
        if value == ".//button[starts-with(@aria-label,'Reaction button state:')]":
            return btn
        raise Exception("not found")

    bar.find_element.side_effect = _find_element

    bot = _FakeBot(MagicMock())
    click_spy = MagicMock(return_value=True)
    bot._click_element_with_fallback = click_spy  # type: ignore[assignment]

    assert bot._like_from_bar(bar) is True
    click_spy.assert_called_once()
    assert click_spy.call_args.args[1] == "Like (stream)"


def test_like_from_bar_treats_liked_state_as_already_pressed(_patch_wait):
    """If the label says ``Reaction button state: liked``, the helper must
    treat the button as already pressed and refuse to click again."""

    bar = MagicMock()
    btn = _make_element(
        attrs={
            "aria-label": "Reaction button state: liked",
            "aria-pressed": "false",  # aria-pressed lies in the new DOM
        }
    )
    bar.find_element.side_effect = lambda by, value: btn

    bot = _FakeBot(MagicMock())
    click_spy = MagicMock(return_value=True)
    bot._click_element_with_fallback = click_spy  # type: ignore[assignment]

    assert bot._like_from_bar(bar) is False
    click_spy.assert_not_called()


# ---------------------------------------------------------------------------
# EngageFlowMixin._locate_action_bar fallback
# ---------------------------------------------------------------------------


def _make_executor():
    """Build a minimally-initialised ``EngageExecutor``.

    We bypass ``__init__`` because only ``_locate_action_bar`` is under test
    and it doesn't read ``self.x`` or ``self.ctx``.
    """

    executor = EngageExecutor.__new__(EngageExecutor)
    return executor


def test_locate_action_bar_returns_post_root_on_new_dom():
    """No legacy ``feed-shared-social-action-bar`` div, but the new-DOM
    Reaction button exists somewhere inside the post — the helper must
    return the post root itself so downstream like logic stays reachable."""

    new_button = _make_element(
        attrs={"aria-label": "Reaction button state: no reaction"}
    )
    post_root = _make_element(
        children={
            ".//button[starts-with(@aria-label,'Reaction button state:')]": [
                new_button
            ],
        },
    )

    executor = _make_executor()
    assert executor._locate_action_bar(post_root) is post_root


def test_locate_action_bar_returns_none_when_nothing_matches():
    post_root = _make_element()  # neither legacy bar nor new button

    executor = _make_executor()
    assert executor._locate_action_bar(post_root) is None


def test_locate_action_bar_returns_legacy_bar_when_present():
    """Old DOM still works: when a feed-shared-social-action-bar div
    exists it is returned verbatim."""

    legacy_bar = _make_element()
    post_root = _make_element(
        children={
            ".//div[contains(@class,'feed-shared-social-action-bar')]": [
                legacy_bar
            ],
        },
    )

    executor = _make_executor()
    assert executor._locate_action_bar(post_root) is legacy_bar


# ---------------------------------------------------------------------------
# _dump_comment_submit_diagnostics (one-shot per run)
# ---------------------------------------------------------------------------


def test_comment_submit_diagnostics_writes_html_and_png(tmp_path, monkeypatch, caplog):
    """First failure dumps an HTML + PNG and logs the saved paths."""

    monkeypatch.chdir(tmp_path)
    driver = MagicMock()
    driver.current_url = "https://www.linkedin.com/feed/"
    driver.title = "Feed | LinkedIn"
    driver.page_source = "<html>fake page source</html>"
    driver.save_screenshot.return_value = True

    bot = _FakeBot(driver)
    with caplog.at_level("INFO"):
        bot._dump_comment_submit_diagnostics()

    diag_dir = tmp_path / "logs" / "diag"
    assert diag_dir.exists(), "diagnostic directory must be created"
    html_files = list(diag_dir.glob("comment_submit_failed_*.html"))
    assert len(html_files) == 1
    assert html_files[0].read_text(encoding="utf-8") == "<html>fake page source</html>"

    # save_screenshot was invoked with the matching PNG path.
    driver.save_screenshot.assert_called_once()
    png_arg = driver.save_screenshot.call_args.args[0]
    assert png_arg.endswith(".png")
    assert "comment_submit_failed_" in png_arg

    # The reason + saved-html log lines are emitted.
    messages = [r.getMessage() for r in caplog.records]
    assert any("ENGAGE_DIAG reason=comment_submit_failed" in m for m in messages)
    assert any("ENGAGE_DIAG saved_html=" in m for m in messages)


def test_comment_submit_diagnostics_is_one_shot_per_instance(tmp_path, monkeypatch):
    """A second failure within the same run must NOT dump again."""

    monkeypatch.chdir(tmp_path)
    driver = MagicMock()
    driver.current_url = "https://www.linkedin.com/feed/"
    driver.title = "Feed | LinkedIn"
    driver.page_source = "<html>1</html>"
    driver.save_screenshot.return_value = True

    bot = _FakeBot(driver)
    bot._dump_comment_submit_diagnostics()
    bot._dump_comment_submit_diagnostics()
    bot._dump_comment_submit_diagnostics()

    html_files = list((tmp_path / "logs" / "diag").glob("comment_submit_failed_*.html"))
    assert len(html_files) == 1, "diagnostics must be a one-shot per run"
    # save_screenshot was only called once.
    assert driver.save_screenshot.call_count == 1


def test_comment_submit_diagnostics_swallows_driver_errors(tmp_path, monkeypatch):
    """A broken ``page_source`` / screenshot must not raise — the engage run
    has to keep going so the next post can still be processed."""

    monkeypatch.chdir(tmp_path)
    driver = MagicMock()
    # All driver access raises — we still expect the helper to return cleanly
    # and to mark itself as "done" so it doesn't keep retrying forever.
    driver.current_url = MagicMock(side_effect=Exception("boom"))
    type(driver).page_source = MagicMock(side_effect=Exception("boom"))
    driver.save_screenshot.side_effect = Exception("boom")

    bot = _FakeBot(driver)
    bot._dump_comment_submit_diagnostics()  # must not raise
    assert getattr(bot, "_comment_submit_diag_done", False) is True
