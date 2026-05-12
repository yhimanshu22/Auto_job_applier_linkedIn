"""Unit tests for ``ProfileActionsMixin.search_profile``.

The implementation drives Selenium, but the public surface (``search_profile``)
is pure logic over the driver's responses. We mock ``self.driver`` so we can
test:

  * Direct-URL strategy succeeds without ever touching the typeahead.
  * Typeahead fallback runs only when direct-URL returns nothing.
  * ``bio_keywords`` selects the matching result over the first one.
  * On total failure a diagnostic dump is attempted (best-effort, no raise).

We never load Selenium; ``self.driver`` is a ``MagicMock`` that returns the
specific elements the assertions need.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from linkedin_automation.linkedin_ui.profile_actions import ProfileActionsMixin


class _FakeBot(ProfileActionsMixin):
    """Minimal host for the mixin so the mocked driver is reachable."""

    def __init__(self, driver):
        self.driver = driver


def _fake_anchor(href: str):
    el = MagicMock()
    el.get_attribute.return_value = href
    return el


def _fake_result(text: str, href: str):
    """Build a fake search-result container with one /in/ anchor inside."""
    container = MagicMock()
    container.text = text
    container.find_element.return_value = _fake_anchor(href)
    return container


def test_search_profile_uses_direct_url_first():
    driver = MagicMock()
    driver.current_url = "https://www.linkedin.com/feed/"
    # First call inside _pick_profile_from_results — return one matching
    # result for the very first selector.
    driver.find_elements.side_effect = [
        [
            _fake_result(
                text="Himanshu Yadav · DevOps",
                href="https://www.linkedin.com/in/himanshu-yadav/",
            )
        ],
    ]

    bot = _FakeBot(driver)
    # ``WebDriverWait`` is patched at the module level so we don't actually
    # poll the (mocked) driver.
    with patch(
        "linkedin_automation.linkedin_ui.profile_actions.WebDriverWait"
    ) as wait_cls:
        wait_cls.return_value.until.return_value = MagicMock()
        url = bot.search_profile("Himanshu Yadav")

    assert url == "https://www.linkedin.com/in/himanshu-yadav/"
    # We navigated exactly once — directly to the people-search URL.
    driver.get.assert_called_once()
    nav_arg = driver.get.call_args.args[0]
    assert "/search/results/people/" in nav_arg
    assert "Himanshu+Yadav" in nav_arg or "Himanshu%20Yadav" in nav_arg


def test_search_profile_falls_back_to_typeahead_when_url_yields_nothing():
    driver = MagicMock()
    driver.current_url = "https://www.linkedin.com/feed/"

    # Direct URL strategy: find_elements returns [] for every selector AND
    # the global /in/ anchor fallback also returns []. Then typeahead
    # strategy: find_elements returns one matching result.
    driver.find_elements.side_effect = (
        [[] for _ in range(7)]
        + [[]]
        + [
            [
                _fake_result(
                    text="Himanshu Y. · Builder",
                    href="https://www.linkedin.com/in/himanshu-y/",
                )
            ]
        ]
    )

    bot = _FakeBot(driver)
    with patch(
        "linkedin_automation.linkedin_ui.profile_actions.WebDriverWait"
    ) as wait_cls:
        # WebDriverWait.until happily returns a clickable element for the
        # typeahead, and a present element for the /in/ probe.
        wait_cls.return_value.until.return_value = MagicMock()
        url = bot.search_profile("Himanshu Y.")

    assert url == "https://www.linkedin.com/in/himanshu-y/"


def test_search_profile_returns_none_when_nothing_matches_and_dumps_diag(
    tmp_path, monkeypatch
):
    driver = MagicMock()
    driver.current_url = "https://www.linkedin.com/feed/"
    driver.title = "LinkedIn"
    driver.page_source = "<html><body>no results</body></html>"
    driver.find_elements.return_value = []  # everything empty everywhere

    # Capture diagnostic dumps under tmp_path so we can assert files were
    # written without polluting the repo.
    monkeypatch.setattr(
        "linkedin_automation.linkedin_ui.profile_actions._DIAG_DIR",
        str(tmp_path),
    )

    bot = _FakeBot(driver)
    with patch(
        "linkedin_automation.linkedin_ui.profile_actions.WebDriverWait"
    ) as wait_cls:
        wait_cls.return_value.until.return_value = MagicMock()
        url = bot.search_profile("Nobody Important")

    assert url is None
    driver.save_screenshot.assert_called_once()
    dumped_html = list(tmp_path.glob("pursue_no_results_*.html"))
    assert dumped_html, "expected an HTML diagnostic dump"


def test_search_profile_picks_bio_keyword_match_over_first_result():
    driver = MagicMock()
    driver.current_url = "https://www.linkedin.com/feed/"

    first = _fake_result(
        text="Himanshu Yadav · Software Engineer",
        href="https://www.linkedin.com/in/first/",
    )
    second = _fake_result(
        text="Himanshu Yadav · DevOps lead at Acme",
        href="https://www.linkedin.com/in/second/",
    )

    # Direct URL strategy returns both candidates on the first selector.
    driver.find_elements.side_effect = [[first, second]]

    bot = _FakeBot(driver)
    with patch(
        "linkedin_automation.linkedin_ui.profile_actions.WebDriverWait"
    ) as wait_cls:
        wait_cls.return_value.until.return_value = MagicMock()
        url = bot.search_profile("Himanshu Yadav", bio_keywords=["devops"])

    assert url == "https://www.linkedin.com/in/second/"


def test_search_profile_rejects_empty_input():
    driver = MagicMock()
    bot = _FakeBot(driver)
    assert bot.search_profile("") is None
    assert bot.search_profile("   ") is None
    assert bot.search_profile(None) is None
    driver.get.assert_not_called()


# ---------------------------------------------------------------------------
# follow_profile + open_profile_posts_view + engage early-bail
# ---------------------------------------------------------------------------


def test_follow_profile_skips_when_already_following():
    """If the page already shows a 'Following' button, we never click."""
    driver = MagicMock()
    driver.find_elements.return_value = [MagicMock()]  # Following button exists

    bot = _FakeBot(driver)
    assert bot.follow_profile() is False
    # We exited via the fast-path; never escalated to WebDriverWait.click.
    driver.execute_script.assert_not_called()


def test_follow_profile_clicks_via_js_when_button_present():
    driver = MagicMock()
    # Fast-path "Following?" probe returns no matches.
    driver.find_elements.return_value = []

    btn = MagicMock()
    btn.text = "Follow"

    bot = _FakeBot(driver)
    with patch(
        "linkedin_automation.linkedin_ui.profile_actions.WebDriverWait"
    ) as wait_cls:
        wait_cls.return_value.until.return_value = btn
        assert bot.follow_profile() is True

    driver.execute_script.assert_called()  # JS click path taken
    args, _ = driver.execute_script.call_args
    assert "click" in args[0]


def test_follow_profile_opens_more_menu_when_top_level_missing():
    """When no top-level Follow exists, expand 'More' and click Follow there.

    We sequence ``WebDriverWait.until`` to:
      1. Raise for every top-level Follow selector (5 of them).
      2. Return a clickable "More" toggle for the first More selector.
      3. Return a clickable Follow button inside the dropdown.
    """
    driver = MagicMock()
    driver.find_elements.return_value = []  # not "Following"

    more_toggle = MagicMock()
    more_toggle.text = "More"
    follow_in_menu = MagicMock()
    follow_in_menu.text = "Follow"

    # Helper to build a side_effect chain on WebDriverWait(...).until.
    untils: list = (
        [Exception()] * 5  # _FOLLOW_BUTTON_SELECTORS top-level scan
        + [more_toggle]    # _MORE_TOGGLE_SELECTORS — first one matches
        + [follow_in_menu] # second pass over _FOLLOW_BUTTON_SELECTORS (inside menu)
    )

    bot = _FakeBot(driver)
    with patch(
        "linkedin_automation.linkedin_ui.profile_actions.WebDriverWait"
    ) as wait_cls:
        instance = wait_cls.return_value

        def _until(_cond):
            v = untils.pop(0)
            if isinstance(v, Exception):
                raise v
            return v

        instance.until.side_effect = _until
        assert bot.follow_profile() is True

    # Two JS clicks expected: one to open More, one to click Follow.
    assert driver.execute_script.call_count >= 2


def test_follow_profile_no_button_anywhere_returns_false_quickly():
    """No Follow on top, no More menu either → warn and return False."""
    driver = MagicMock()
    driver.find_elements.return_value = []  # not "Following"

    bot = _FakeBot(driver)
    with patch(
        "linkedin_automation.linkedin_ui.profile_actions.WebDriverWait"
    ) as wait_cls:
        # Every wait raises.
        wait_cls.return_value.until.side_effect = Exception("not clickable")
        assert bot.follow_profile() is False


def test_open_profile_posts_view_navigates_to_recent_activity():
    """We now deep-link to ``/recent-activity/all/`` instead of clicking."""
    driver = MagicMock()
    driver.current_url = "https://www.linkedin.com/in/williamhgates/"

    bot = _FakeBot(driver)
    with patch(
        "linkedin_automation.linkedin_ui.profile_actions.WebDriverWait"
    ) as wait_cls:
        wait_cls.return_value.until.return_value = MagicMock()
        assert bot.open_profile_posts_view() is True

    driver.get.assert_called_once_with(
        "https://www.linkedin.com/in/williamhgates/recent-activity/all/"
    )


def test_open_profile_posts_view_is_noop_when_already_there():
    driver = MagicMock()
    driver.current_url = (
        "https://www.linkedin.com/in/williamhgates/recent-activity/all/"
    )
    bot = _FakeBot(driver)
    assert bot.open_profile_posts_view() is True
    driver.get.assert_not_called()
