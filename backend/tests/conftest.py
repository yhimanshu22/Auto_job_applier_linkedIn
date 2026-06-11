import os
from pathlib import Path

# Set before db_manager imports utils.encryption (no hardcoded app key in source).
os.environ.setdefault(
    "ENCRYPTION_KEY", "XFtHFGnbGxBxIpsi0IUUxlz7U6v9Dtf28dUCO7a-FsM="
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_manager import db
from models import Base

# Ephemeral SQLite DB for tests (same folder as conftest for predictable cleanup)
TEST_DB_PATH = Path(__file__).resolve().parent / "test_data.db"


def _sqlite_url(path: Path) -> str:
    # Absolute URL form works on Windows when path uses forward slashes
    return "sqlite:///" + path.as_posix()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Point the process-wide ``db`` singleton at a fresh test SQLite file.

    ``DatabaseManager`` uses SQLAlchemy (engine + sessionmaker), not ``conn``.
    """
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except OSError:
            pass

    test_url = _sqlite_url(TEST_DB_PATH)

    # Drop pooled connections to any previous DB (e.g. backend/data.db from imports)
    db.engine.dispose()

    db.db_url = test_url
    db.engine = create_engine(
        test_url,
        connect_args={"check_same_thread": False},
    )
    db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db.engine)

    Base.metadata.create_all(bind=db.engine)

    yield db

    db.engine.dispose()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except OSError:
            pass


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """Clear LinkedIn env vars so bot-limit tests stay deterministic."""
    for key in list(os.environ.keys()):
        if key.startswith("LINKEDIN_USERNAME_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def auth_as(monkeypatch):
    """Simulate a verified NextAuth session for the given email."""

    def _set(email: str):
        async def _session_email(_request):
            return email

        monkeypatch.setattr(
            "utils.user_resolution._session_email", _session_email
        )

    return _set


@pytest.fixture
def client():
    """FastAPI test client (imports ``server.app`` after DB fixture rewires ``db``)."""
    from server import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_db():
    """Shared ``DatabaseManager`` singleton (already bound to test SQLite)."""
    return db
