"""
Tests for backend/auth_middleware.py

Verifies JWT decoding, the require_auth decorator, and waitlist-mode enforcement.
All tests use the in-memory SQLite DB provided by the autouse fixture.
"""

import os
import time

import jwt
import pytest
from flask import Flask, jsonify

from tests.conftest import TEST_JWT_SECRET, make_expired_token, make_token

# ---------------------------------------------------------------------------
# Helpers: build a minimal Flask app that uses require_auth
# ---------------------------------------------------------------------------

def _make_test_flask_app():
    """Return a tiny Flask app with one protected route for testing."""
    import importlib
    # Re-import so the module picks up the test env vars
    import auth_middleware as am
    importlib.reload(am)

    test_app = Flask(__name__)
    test_app.config["TESTING"] = True

    @test_app.route("/protected")
    @am.require_auth
    def protected(user_id):
        return jsonify({"user_id": user_id})

    return test_app


@pytest.fixture()
def auth_app(isolated_sqlite_db, monkeypatch):
    monkeypatch.setenv("NEXTAUTH_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("WAITLIST_MODE", "false")
    return _make_test_flask_app()


@pytest.fixture()
def auth_client(auth_app):
    return auth_app.test_client()


@pytest.fixture()
def waitlist_app(isolated_sqlite_db, monkeypatch):
    monkeypatch.setenv("NEXTAUTH_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("WAITLIST_MODE", "true")
    import auth_middleware as am
    import importlib
    importlib.reload(am)

    test_app = Flask(__name__)
    test_app.config["TESTING"] = True

    @test_app.route("/protected")
    @am.require_auth
    def protected(user_id):
        return jsonify({"user_id": user_id})

    return test_app


@pytest.fixture()
def waitlist_client(waitlist_app):
    return waitlist_app.test_client()


# ---------------------------------------------------------------------------
# _decode_request_token / get_user_id_from_request (via HTTP layer)
# ---------------------------------------------------------------------------

class TestRequireAuth:
    def test_no_auth_header_returns_401(self, auth_client):
        resp = auth_client.get("/protected")
        assert resp.status_code == 401
        assert resp.get_json()["error"] == "Unauthorized"

    def test_malformed_bearer_returns_401(self, auth_client):
        resp = auth_client.get("/protected", headers={"Authorization": "NotBearer abc"})
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, auth_client):
        resp = auth_client.get(
            "/protected",
            headers={"Authorization": "Bearer this-is-not-a-valid-jwt"},
        )
        assert resp.status_code == 401

    def test_wrong_secret_returns_401(self, auth_client):
        bad_token = make_token(secret="wrong-secret")
        resp = auth_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        assert resp.status_code == 401

    def test_expired_token_returns_401(self, auth_client):
        expired = make_expired_token()
        resp = auth_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert resp.status_code == 401

    def test_valid_token_returns_200_with_user_id(self, auth_client):
        token = make_token(user_id="user-abc")
        resp = auth_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["user_id"] == "user-abc"

    def test_bearer_prefix_is_required(self, auth_client):
        token = make_token()
        # Provide token without "Bearer " prefix
        resp = auth_client.get(
            "/protected",
            headers={"Authorization": token},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Waitlist mode
# ---------------------------------------------------------------------------

class TestWaitlistMode:
    def test_blocked_email_returns_403_waitlist(self, waitlist_client):
        token = make_token(user_id="u1", email="blocked@example.com")
        resp = waitlist_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        body = resp.get_json()
        assert body["code"] == "waitlist"

    def test_allowed_email_returns_200(self, waitlist_client, isolated_sqlite_db):
        isolated_sqlite_db.add_allowed_email("vip@example.com")
        token = make_token(user_id="u2", email="vip@example.com")
        resp = waitlist_client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["user_id"] == "u2"

    def test_no_secret_configured_returns_401(self, monkeypatch, isolated_sqlite_db):
        monkeypatch.setenv("NEXTAUTH_SECRET", "")
        monkeypatch.setenv("WAITLIST_MODE", "false")

        import auth_middleware as am
        import importlib
        importlib.reload(am)

        test_app = Flask(__name__)
        test_app.config["TESTING"] = True

        @test_app.route("/protected")
        @am.require_auth
        def protected(user_id):
            return jsonify({"user_id": user_id})

        with test_app.test_client() as c:
            token = make_token()
            resp = c.get("/protected", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 401
