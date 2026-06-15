from services.chrome_ports import (
    BASE_CHROME_DEBUG_PORT,
    account_port_for_bot_id,
    account_port_for_slot,
    resolve_chrome_debug_port,
)


def test_account_port_for_slot():
    assert account_port_for_slot(1) == 9222
    assert account_port_for_slot(2) == 9223
    assert account_port_for_slot(3) == 9224


def test_account_port_for_bot_id():
    assert account_port_for_bot_id("main") == 9222
    assert account_port_for_bot_id("1") == 9223
    assert account_port_for_bot_id("2") == 9224
    assert account_port_for_bot_id(None) == 9222


def test_resolve_chrome_debug_port_env(monkeypatch):
    monkeypatch.delenv("CHROME_DEBUG_PORT", raising=False)
    monkeypatch.delenv("ACCOUNT_PORT", raising=False)
    monkeypatch.setenv("BOT_ID", "2")
    assert resolve_chrome_debug_port() == 9224

    monkeypatch.setenv("CHROME_DEBUG_PORT", "9333")
    assert resolve_chrome_debug_port() == 9333


def test_list_supervisor_accounts_assigns_account_port(test_db):
    uid = "ports-user@test.com"
    test_db.set_config("LINKEDIN_USERNAME", "primary@test.com", "secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD", "secret1", "secrets", user_id=uid)
    test_db.set_config("LINKEDIN_USERNAME_1", "extra@test.com", "secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD_1", "secret2", "secrets", user_id=uid)

    from services.linkedin_env import list_supervisor_accounts

    accounts = list_supervisor_accounts(user_id=uid)
    assert accounts[0]["account_port"] == BASE_CHROME_DEBUG_PORT
    assert accounts[1]["account_port"] == BASE_CHROME_DEBUG_PORT + 1
