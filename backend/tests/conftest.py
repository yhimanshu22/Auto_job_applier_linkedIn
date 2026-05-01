import pytest
import os
from fastapi.testclient import TestClient
from server import app
from db_manager import DatabaseManager

# Use the test database path from environment or default
TEST_DB_PATH = "./test_data.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure the test database is clean before running tests."""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    # Re-initialize the DB
    db = DatabaseManager(TEST_DB_PATH)
    yield db
    # Clean up after tests
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except:
            pass

@pytest.fixture
def client():
    """Provides a FastAPI test client."""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_db():
    """Provides access to the database manager."""
    from db_manager import db
    return db
