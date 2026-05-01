import pytest
import os
from fastapi.testclient import TestClient
from db_manager import db, DatabaseManager

# Use the test database path
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_data.db")

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure the test database is clean and singleton db uses it."""
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except:
            pass
            
    # Redirect the singleton db to the test database
    db.conn.close()
    db.db_path = TEST_DB_PATH
    import sqlite3
    db.conn = sqlite3.connect(TEST_DB_PATH, check_same_thread=False)
    db.conn.row_factory = sqlite3.Row
    db.create_tables()
    
    yield db
    
    db.conn.close()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except:
            pass

@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """Clear LinkedIn env vars to ensure predictable bot limits in tests."""
    for key in list(os.environ.keys()):
        if key.startswith("LINKEDIN_USERNAME_"):
            monkeypatch.delenv(key, raising=False)

@pytest.fixture
def client():
    """Provides a FastAPI test client."""
    from server import app
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_db():
    """Provides access to the database manager."""
    return db
