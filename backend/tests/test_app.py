"""
Flask API integration tests for backend/app.py.

External services (Twilio, ElevenLabs, Google, chat AI) are mocked so no
credentials are needed. The autouse `isolated_sqlite_db` fixture in conftest.py
provides a fresh in-memory SQLite DB for each test.
"""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import make_token, TEST_JWT_SECRET


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def valid_token():
    return make_token(user_id="user-test", email="test@example.com")


@pytest.fixture()
def bearer(valid_token):
    return {"Authorization": f"Bearer {valid_token}", "Content-Type": "application/json"}


# Patch external service factories once for the whole module to avoid credential errors
@pytest.fixture(autouse=True)
def mock_external_services(mocker):
    mocker.patch("app.get_google_service", return_value=MagicMock())
    mocker.patch("app.get_elevenlabs_service", return_value=MagicMock())
    mocker.patch("app.get_twilio_service", return_value=MagicMock())


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_returns_healthy_status(self, client):
        resp = client.get("/health")
        assert resp.get_json()["status"] == "healthy"

    def test_returns_service_name(self, client):
        resp = client.get("/health")
        assert resp.get_json()["service"] == "callpilot"


# ---------------------------------------------------------------------------
# Debug auth endpoint
# ---------------------------------------------------------------------------

class TestDebugAuthConfigured:
    def test_returns_200(self, client):
        resp = client.get("/api/debug/auth-configured")
        assert resp.status_code == 200

    def test_auth_configured_true_when_secret_set(self, client):
        # conftest sets NEXTAUTH_SECRET to TEST_JWT_SECRET
        resp = client.get("/api/debug/auth-configured")
        assert resp.get_json()["auth_configured"] is True


# ---------------------------------------------------------------------------
# Waitlist
# ---------------------------------------------------------------------------

class TestWaitlistSignup:
    def test_valid_signup_returns_200(self, client):
        resp = client.post(
            "/api/waitlist",
            json={"email": "new@example.com", "name": "New User"},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["ok"] is True

    def test_response_contains_email(self, client):
        resp = client.post(
            "/api/waitlist",
            json={"email": "Another@Example.COM", "name": "Upper"},
        )
        body = resp.get_json()
        assert body["email"] == "another@example.com"

    def test_missing_email_returns_400(self, client):
        resp = client.post("/api/waitlist", json={"name": "No Email"})
        assert resp.status_code == 400

    def test_invalid_email_returns_400(self, client):
        resp = client.post(
            "/api/waitlist",
            json={"email": "not-an-email", "name": "Bad Email"},
        )
        assert resp.status_code == 400

    def test_empty_json_returns_400(self, client):
        resp = client.post("/api/waitlist", json={})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Task creation and retrieval
# ---------------------------------------------------------------------------

class TestTask:
    def test_create_task_no_auth_returns_401(self, client):
        resp = client.post("/api/task")
        assert resp.status_code == 401

    def test_create_task_with_auth_returns_200(self, client, bearer):
        resp = client.post("/api/task", headers=bearer)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "task_id" in body
        assert body["status"] == "gathering_info"

    def test_get_task_not_found_returns_404(self, client, bearer):
        resp = client.get("/api/task/nonexistent-task-id", headers=bearer)
        assert resp.status_code == 404

    def test_get_task_wrong_user_returns_404(self, client, isolated_sqlite_db):
        # Create task for user-A
        import database as db
        tid = str(uuid.uuid4())
        db.create_task(tid, user_id="user-A")

        # user-B tries to retrieve it
        token_b = make_token(user_id="user-B", email="b@example.com")
        headers_b = {"Authorization": f"Bearer {token_b}", "Content-Type": "application/json"}
        resp = client.get(f"/api/task/{tid}", headers=headers_b)
        assert resp.status_code == 404

    def test_get_task_own_task_returns_200(self, client, bearer, isolated_sqlite_db):
        import database as db
        tid = str(uuid.uuid4())
        db.create_task(tid, user_id="user-test")
        resp = client.get(f"/api/task/{tid}", headers=bearer)
        assert resp.status_code == 200
        assert resp.get_json()["task_id"] == tid


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------

class TestChat:
    def test_chat_no_auth_returns_401(self, client):
        resp = client.post("/api/chat", json={"task_id": "x", "message": "hello"})
        assert resp.status_code == 401

    def test_chat_missing_task_id_returns_400(self, client, bearer):
        resp = client.post("/api/chat", json={"message": "hello"}, headers=bearer)
        assert resp.status_code == 400

    def test_chat_missing_message_returns_400(self, client, bearer, isolated_sqlite_db):
        import database as db
        tid = str(uuid.uuid4())
        db.create_task(tid, user_id="user-test")
        resp = client.post("/api/chat", json={"task_id": tid}, headers=bearer)
        assert resp.status_code == 400

    def test_chat_nonexistent_task_returns_404(self, client, bearer):
        resp = client.post(
            "/api/chat",
            json={"task_id": "does-not-exist", "message": "hello"},
            headers=bearer,
        )
        assert resp.status_code == 404

    def test_chat_returns_reply(self, client, bearer, isolated_sqlite_db, mocker):
        import database as db
        tid = str(uuid.uuid4())
        db.create_task(tid, user_id="user-test")

        # Mock the AI chat service
        mocker.patch(
            "app.chat_service_chat",
            return_value=(
                "I can help with that! What city are you in?",
                {"service_type": "dentist"},
                "gathering_info",
            ),
        )

        resp = client.post(
            "/api/chat",
            json={"task_id": tid, "message": "I need a dentist"},
            headers=bearer,
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert "reply" in body
        assert "task_status" in body
        assert body["task_id"] == tid


# ---------------------------------------------------------------------------
# Booking request
# ---------------------------------------------------------------------------

class TestBookingRequest:
    def test_no_auth_returns_401(self, client):
        resp = client.post(
            "/api/booking/request",
            json={"service_type": "dentist", "location": "Boston", "timeframe": "this week"},
        )
        assert resp.status_code == 401

    def test_creates_booking_returns_processing(self, client, bearer, mocker):
        # Prevent background thread from actually calling external APIs
        mocker.patch("threading.Thread")

        resp = client.post(
            "/api/booking/request",
            json={"service_type": "dentist", "location": "Boston", "timeframe": "this week"},
            headers=bearer,
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "processing"
        assert "booking_id" in body

    def test_created_booking_stored_in_db(self, client, bearer, isolated_sqlite_db, mocker):
        mocker.patch("threading.Thread")

        resp = client.post(
            "/api/booking/request",
            json={"service_type": "doctor", "location": "Cambridge", "timeframe": "tomorrow"},
            headers=bearer,
        )
        booking_id = resp.get_json()["booking_id"]
        stored = isolated_sqlite_db.get_booking(booking_id, user_id="user-test")
        assert stored is not None
        assert stored["service_type"] == "doctor"


# ---------------------------------------------------------------------------
# Get booking status
# ---------------------------------------------------------------------------

class TestGetBookingStatus:
    def test_no_auth_returns_401(self, client):
        resp = client.get("/api/booking/some-id")
        assert resp.status_code == 401

    def test_not_found_returns_404(self, client, bearer):
        resp = client.get(f"/api/booking/{uuid.uuid4()}", headers=bearer)
        assert resp.status_code == 404

    def test_returns_booking_data(self, client, bearer, isolated_sqlite_db):
        import database as db
        bid = str(uuid.uuid4())
        db.create_booking(bid, "dentist", "Boston", "today", {}, user_id="user-test")

        resp = client.get(f"/api/booking/{bid}", headers=bearer)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["booking_id"] == bid
        assert body["status"] == "processing"

    def test_wrong_user_cannot_access_booking(self, client, isolated_sqlite_db):
        import database as db
        bid = str(uuid.uuid4())
        db.create_booking(bid, "dentist", "Boston", "today", {}, user_id="alice")

        token_bob = make_token(user_id="bob", email="bob@example.com")
        resp = client.get(
            f"/api/booking/{bid}",
            headers={"Authorization": f"Bearer {token_bob}"},
        )
        assert resp.status_code == 404

    def test_processing_booking_returns_message(self, client, bearer, isolated_sqlite_db):
        import database as db
        bid = str(uuid.uuid4())
        db.create_booking(bid, "dentist", "Boston", "today", {}, user_id="user-test")

        resp = client.get(f"/api/booking/{bid}", headers=bearer)
        body = resp.get_json()
        assert "message" in body


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

class TestDashboardStats:
    def test_no_auth_returns_401(self, client):
        resp = client.get("/api/dashboard/stats")
        assert resp.status_code == 401

    def test_returns_stats_shape(self, client, bearer):
        resp = client.get("/api/dashboard/stats", headers=bearer)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "stats" in body
        stats = body["stats"]
        assert "total_bookings" in stats
        assert "completed" in stats
        assert "processing" in stats

    def test_empty_db_stats_are_zero(self, client, bearer):
        resp = client.get("/api/dashboard/stats", headers=bearer)
        body = resp.get_json()
        assert body["stats"]["total_bookings"] == 0


# ---------------------------------------------------------------------------
# Dashboard bookings
# ---------------------------------------------------------------------------

class TestDashboardBookings:
    def test_no_auth_returns_401(self, client):
        resp = client.get("/api/dashboard/bookings")
        assert resp.status_code == 401

    def test_returns_bookings_list(self, client, bearer):
        resp = client.get("/api/dashboard/bookings", headers=bearer)
        assert resp.status_code == 200
        assert "bookings" in resp.get_json()

    def test_only_returns_own_bookings(self, client, bearer, isolated_sqlite_db):
        import database as db
        db.create_booking(str(uuid.uuid4()), "dentist", "Boston", "today", {}, user_id="user-test")
        db.create_booking(str(uuid.uuid4()), "doctor", "NYC", "tomorrow", {}, user_id="other-user")

        resp = client.get("/api/dashboard/bookings", headers=bearer)
        bookings = resp.get_json()["bookings"]
        assert len(bookings) == 1
        assert bookings[0]["user_id"] == "user-test"


# ---------------------------------------------------------------------------
# Twilio voice webhook
# ---------------------------------------------------------------------------

class TestTwilioVoiceWebhook:
    def test_step_0_returns_xml(self, client):
        resp = client.get(
            "/api/twilio/voice",
            query_string={"step": "0", "service_type": "dentist", "timeframe": "this week"},
        )
        assert resp.status_code == 200
        assert "application/xml" in resp.content_type
        assert b"<Response>" in resp.data

    def test_step_1_returns_follow_up_xml(self, client):
        resp = client.get(
            "/api/twilio/voice",
            query_string={"step": "1", "service_type": "doctor", "timeframe": "tomorrow"},
        )
        assert resp.status_code == 200
        assert b"<Response>" in resp.data

    def test_step_2_returns_thank_and_hangup(self, client):
        resp = client.get(
            "/api/twilio/voice",
            query_string={"step": "2", "service_type": "doctor", "timeframe": "today"},
        )
        assert resp.status_code == 200
        assert b"<Hangup" in resp.data


# ---------------------------------------------------------------------------
# ElevenLabs webhook
# ---------------------------------------------------------------------------

class TestElevenLabsWebhook:
    def test_invalid_json_returns_400(self, client):
        resp = client.post(
            "/api/webhooks/elevenlabs",
            data=b"not-json",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_missing_conversation_id_returns_200(self, client):
        resp = client.post(
            "/api/webhooks/elevenlabs",
            json={"type": "post_call_transcription", "data": {}},
        )
        assert resp.status_code == 200

    def test_unknown_conversation_id_still_returns_200(self, client):
        resp = client.post(
            "/api/webhooks/elevenlabs",
            json={
                "type": "post_call_transcription",
                "data": {"conversation_id": "unknown-conv-id"},
            },
        )
        assert resp.status_code == 200

    def test_known_conversation_updates_booking(self, client, isolated_sqlite_db):
        import database as db
        bid = str(uuid.uuid4())
        conv_id = "conv-" + str(uuid.uuid4())
        db.create_booking(bid, "dentist", "Boston", "today", {})
        db.update_booking_results(bid, [{"conversation_id": conv_id, "call_status": "in_progress"}])
        # Status must be 'processing' to be found by get_booking_by_conversation_id
        db.update_booking_status(bid, "processing", [{"conversation_id": conv_id, "call_status": "in_progress"}])

        payload = {
            "type": "post_call_transcription",
            "data": {
                "conversation_id": conv_id,
                "analysis": {"call_successful": "success"},
                "metadata": {"call_duration_secs": 60},
            },
        }
        resp = client.post("/api/webhooks/elevenlabs", json=payload)
        assert resp.status_code == 200

        booking = db.get_booking(bid)
        assert booking["status"] == "completed"
