"""Chrome profile path helpers shared by the job bot and automation."""

from services.chrome_profiles import (
    bot_chrome_profile_dir,
    linkedin_email_to_bot_id,
    resolve_automation_chrome_profile,
)


def test_linkedin_email_to_bot_id_primary(test_db):
    uid = "user@example.com"
    test_db.set_config("LINKEDIN_USERNAME", uid, category="secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD", "pw", category="secrets", user_id=uid)

    assert linkedin_email_to_bot_id(user_id=uid, linkedin_email=uid) == "main"


def test_linkedin_email_to_bot_id_extra_slot(test_db):
    uid = "owner@example.com"
    test_db.set_config("LINKEDIN_USERNAME", "primary@example.com", category="secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD", "pw0", category="secrets", user_id=uid)
    test_db.set_config("LINKEDIN_USERNAME_2", "extra@example.com", category="secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD_2", "pw2", category="secrets", user_id=uid)

    assert linkedin_email_to_bot_id(user_id=uid, linkedin_email="extra@example.com") == "2"


def test_resolve_automation_chrome_profile_requires_on_disk(test_db, monkeypatch, tmp_path):
    monkeypatch.setenv("LINKDAPPLY_USER_DATA", str(tmp_path))
    uid = "user@example.com"
    test_db.set_config("LINKEDIN_USERNAME", uid, category="secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD", "pw", category="secrets", user_id=uid)

    assert resolve_automation_chrome_profile(user_id=uid, linkedin_email=uid) is None

    (tmp_path / "chrome_profiles" / "main").mkdir(parents=True)
    resolved = resolve_automation_chrome_profile(user_id=uid, linkedin_email=uid)
    assert resolved is not None
    assert resolved["bot_id"] == "main"
    assert resolved["profile_dir"] == bot_chrome_profile_dir("main")
