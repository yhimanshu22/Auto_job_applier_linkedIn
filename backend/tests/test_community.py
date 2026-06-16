from unittest.mock import patch

from fastapi.testclient import TestClient


def test_list_community_posts_seeds_defaults(client: TestClient):
    response = client.get("/api/community/posts")
    assert response.status_code == 200
    posts = response.json()["posts"]
    assert len(posts) >= 3
    assert posts[0]["body"]
    assert "title" not in posts[0]
    assert isinstance(posts[0]["replies"], list)


def test_create_post_and_reply(client: TestClient):
    with patch("routes.community.send_community_notification", return_value=False):
        post_res = client.post(
            "/api/community/posts",
            json={
                "author_name": "Test User",
                "body": "I am new to LinkdApply and want to understand the best filter setup.",
            },
        )
    assert post_res.status_code == 200
    post_id = post_res.json()["post"]["id"]

    reply_res = client.post(
        f"/api/community/posts/{post_id}/replies",
        json={
            "author_name": "Helper",
            "body": "Start with remote + Easy Apply, then narrow by keywords.",
        },
    )
    assert reply_res.status_code == 200

    thread = client.get(f"/api/community/posts/{post_id}").json()
    assert thread["reply_count"] == 1
    assert thread["replies"][0]["body"].startswith("Start with remote")
