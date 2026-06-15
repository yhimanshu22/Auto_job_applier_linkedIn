from services.linkedin_env import list_supervisor_accounts


def test_list_supervisor_accounts_from_db(test_db):
    uid = "supervisor-user@test.com"
    test_db.set_config("username", "primary@test.com", "secrets", user_id=uid)
    test_db.set_config("password", "secret1", "secrets", user_id=uid)
    test_db.set_config(
        "linkedin_extra_accounts",
        [
            {"username": "extra@test.com", "password": "secret2"},
            {"username": "no-password@test.com"},
        ],
        "secrets",
        user_id=uid,
    )

    accounts = list_supervisor_accounts(user_id=uid)
    assert len(accounts) == 2
    assert accounts[0] == {
        "id": "main",
        "username": "primary@test.com",
        "password": "secret1",
    }
    assert accounts[1]["username"] == "extra@test.com"
    assert accounts[1]["password"] == "secret2"


def test_list_supervisor_accounts_legacy_code_mode_keys(test_db):
    """secrets.py code mode stores LINKEDIN_USERNAME_1 / LINKEDIN_PASSWORD_1 in DB."""
    uid = "legacy-user@test.com"
    test_db.set_config(
        "LINKEDIN_USERNAME_1", "yhimanshu220456@gmail.com", "secrets", user_id=uid
    )
    test_db.set_config("LINKEDIN_PASSWORD_1", "secret1", "secrets", user_id=uid)
    test_db.set_config("LINKEDIN_USERNAME_2", "himu09854@gmail.com", "secrets", user_id=uid)
    test_db.set_config("LINKEDIN_PASSWORD_2", "secret2", "secrets", user_id=uid)

    accounts = list_supervisor_accounts(user_id=uid)
    assert len(accounts) == 2
    emails = {a["username"] for a in accounts}
    assert "yhimanshu220456@gmail.com" in emails
    assert "himu09854@gmail.com" in emails


def test_list_supervisor_accounts_empty_without_password(test_db):
    uid = "empty-user@test.com"
    test_db.set_config("username", "only@test.com", "secrets", user_id=uid)

    assert list_supervisor_accounts(user_id=uid) == []
