def test_get_linkedin_accounts_lists_saved_accounts(client, test_db, auth_as):
    auth_as("secrets-user@test.com")
    test_db.set_config("username", "primary@test.com", "secrets", user_id="secrets-user@test.com")
    test_db.set_config("password", "secret1", "secrets", user_id="secrets-user@test.com")
    test_db.set_config(
        "linkedin_extra_accounts",
        [
            {"username": "extra1@test.com", "password": "secret2"},
            {"username": "extra2@test.com", "password": "secret3"},
        ],
        "secrets",
        user_id="secrets-user@test.com",
    )

    res = client.get("/api/linkedin-accounts")
    assert res.status_code == 200
    body = res.json()
    assert body["account_count"] == 3
    assert len(body["accounts"]) == 3
    assert body["account_count"] == len(body["accounts"])
    usernames = [a["username"] for a in body["accounts"]]
    assert "primary@test.com" in usernames
    assert "extra1@test.com" in usernames
    assert "extra2@test.com" in usernames
    primary = next(a for a in body["accounts"] if a["primary"])
    assert primary["username"] == "primary@test.com"
    assert primary["has_password"] is True
    assert all(a["deletable"] for a in body["accounts"])


def test_delete_extra_linkedin_account(client, test_db, auth_as):
    auth_as("del-user@test.com")
    test_db.set_config("username", "keep@test.com", "secrets", user_id="del-user@test.com")
    test_db.set_config("password", "pw1", "secrets", user_id="del-user@test.com")
    test_db.set_config(
        "linkedin_extra_accounts",
        [{"username": "remove@test.com", "password": "pw2"}],
        "secrets",
        user_id="del-user@test.com",
    )

    res = client.delete("/api/linkedin-accounts?username=remove@test.com")
    assert res.status_code == 200
    assert res.json()["account_count"] == 1

    listed = client.get("/api/linkedin-accounts").json()
    names = [a["username"] for a in listed["accounts"]]
    assert "remove@test.com" not in names
    assert "keep@test.com" in names


def test_delete_primary_promotes_first_extra(client, test_db, auth_as):
    auth_as("promo-user@test.com")
    test_db.set_config("username", "old@test.com", "secrets", user_id="promo-user@test.com")
    test_db.set_config("password", "pw1", "secrets", user_id="promo-user@test.com")
    test_db.set_config(
        "linkedin_extra_accounts",
        [{"username": "next@test.com", "password": "pw2"}],
        "secrets",
        user_id="promo-user@test.com",
    )

    res = client.delete("/api/linkedin-accounts?username=old@test.com")
    assert res.status_code == 200

    listed = client.get("/api/linkedin-accounts").json()
    primary = next(a for a in listed["accounts"] if a["primary"])
    assert primary["username"] == "next@test.com"
    assert "old@test.com" not in [a["username"] for a in listed["accounts"]]


def test_account_count_matches_deduplicated_accounts(client, test_db, auth_as, monkeypatch):
    """DB + .env overlap must not inflate account_count above listed accounts."""
    auth_as("dedup-user@test.com")
    test_db.set_config("username", "primary@test.com", "secrets", user_id="dedup-user@test.com")
    test_db.set_config("password", "pw1", "secrets", user_id="dedup-user@test.com")
    test_db.set_config(
        "linkedin_extra_accounts",
        [{"username": "extra@test.com", "password": "pw2"}],
        "secrets",
        user_id="dedup-user@test.com",
    )
    # Same emails as DB, but under separate env slots (common when .env and dashboard overlap).
    monkeypatch.setenv("LINKEDIN_USERNAME_1", "primary@test.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD_1", "envpw1")
    monkeypatch.setenv("LINKEDIN_USERNAME_2", "extra@test.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD_2", "envpw2")

    res = client.get("/api/linkedin-accounts")
    assert res.status_code == 200
    body = res.json()
    assert body["account_count"] == len(body["accounts"]) == 2
    assert sorted(a["username"] for a in body["accounts"]) == [
        "extra@test.com",
        "primary@test.com",
    ]
