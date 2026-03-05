"""
Shared pytest fixtures for CallPilot backend tests.

All tests run against an in-memory (temp-file) SQLite database — no
Firestore, Twilio, ElevenLabs, or Google credentials needed.
"""

import os
import sys
import time
import uuid

import jwt
import pytest

# ---------------------------------------------------------------------------
# Ensure the backend package root is importable before any test imports
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ---------------------------------------------------------------------------
# Force SQLite and disable external services BEFORE importing backend modules
# ---------------------------------------------------------------------------
TEST_JWT_SECRET = "test-secret-key"


def _set_test_env(tmp_db_path: str):
    """Patch os.environ so every backend module sees test settings."""
    os.environ["USE_SQLITE"] = "true"
    os.environ["NEXTAUTH_SECRET"] = TEST_JWT_SECRET
    os.environ["WAITLIST_MODE"] = "false"
    # Remove any real GCP / Twilio / ElevenLabs vars that might be present
    for key in (
        "GOOGLE_CLOUD_PROJECT",
        "GCLOUD_PROJECT",
        "GCP_PROJECT",
        "ELEVENLABS_AGENT_ID",
        "ELEVENLABS_AGENT_PHONE_NUMBER_ID",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
    ):
        os.environ.pop(key, None)


@pytest.fixture(autouse=True)
def isolated_sqlite_db(tmp_path, monkeypatch):
    """
    Each test gets a fresh, empty SQLite database in a temp directory.
    Resets the module-level Firestore cache so _use_firestore() re-evaluates.
    """
    db_path = str(tmp_path / "test_callpilot.db")
    _set_test_env(db_path)

    # Patch the module-level path and cache in database.py
    import database as db_module

    monkeypatch.setattr(db_module, "_SQLITE_PATH", db_path)
    monkeypatch.setattr(db_module, "_USE_FIRESTORE", None)

    db_module.init_db()
    yield db_module


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def make_token(user_id: str = "user-123", email: str = "test@example.com", secret: str = TEST_JWT_SECRET) -> str:
    """Return a signed HS256 JWT mimicking what NextAuth produces."""
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def make_expired_token(user_id: str = "user-123") -> str:
    payload = {
        "sub": user_id,
        "email": "test@example.com",
        "iat": int(time.time()) - 7200,
        "exp": int(time.time()) - 3600,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# Flask app fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def _app_module():
    """Import and return the Flask app once per test session."""
    # Environment is already patched by the autouse fixture at function scope,
    # but we need it set before the first import of app.py.
    os.environ.setdefault("USE_SQLITE", "true")
    os.environ.setdefault("NEXTAUTH_SECRET", TEST_JWT_SECRET)
    os.environ.setdefault("WAITLIST_MODE", "false")

    import app as flask_app_module
    return flask_app_module


@pytest.fixture()
def flask_app(isolated_sqlite_db, _app_module):
    """Flask test app with TESTING=True and a fresh DB per test."""
    app = _app_module.app
    app.config["TESTING"] = True
    return app


@pytest.fixture()
def client(flask_app):
    """Flask test client."""
    return flask_app.test_client()


@pytest.fixture()
def auth_headers():
    """Authorization headers for a default test user."""
    token = make_token()
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture()
def user_id():
    return "user-123"
