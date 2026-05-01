import pytest

def test_get_config_personals(client):
    response = client.get("/api/config/personals")
    assert response.status_code == 200
    assert "content" in response.json()

def test_save_config_invalid_category(client):
    response = client.post(
        "/api/config/invalid",
        json={"content": "{}"}
    )
    assert response.status_code == 400
    assert "Invalid config category" in response.json()["detail"]

def test_save_and_read_config(client):
    test_content = 'name = "Test User"\nemail = "test@example.com"'
    # Save
    save_res = client.post(
        "/api/config/personals",
        json={"content": test_content}
    )
    assert save_res.status_code == 200
    
    # Read back
    read_res = client.get("/api/config/personals")
    assert read_res.status_code == 200
    assert 'name = "Test User"' in read_res.json()["content"]
    assert 'email = "test@example.com"' in read_res.json()["content"]

def test_save_list_config(client):
    test_content = 'keywords = ["Python", "React"]'
    client.post("/api/config/search", json={"content": test_content})
    
    read_res = client.get("/api/config/search")
    content = read_res.json()["content"]
    assert 'keywords =' in content
    assert 'Python' in content
    assert 'React' in content
