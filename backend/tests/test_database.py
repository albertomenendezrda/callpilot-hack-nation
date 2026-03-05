"""
Tests for backend/database.py (SQLite path).

The autouse `isolated_sqlite_db` fixture in conftest.py forces USE_SQLITE=true
and gives each test a fresh temp database, so tests are fully isolated.
"""

import uuid

import pytest

import database as db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def new_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

class TestBookings:
    def test_create_booking_returns_dict(self):
        booking = db.create_booking(new_id(), "dentist", "Boston, MA", "this week", {})
        assert isinstance(booking, dict)
        assert booking["status"] == "processing"
        assert booking["service_type"] == "dentist"

    def test_create_booking_stores_user_id(self):
        bid = new_id()
        db.create_booking(bid, "doctor", "Cambridge, MA", "tomorrow", {}, user_id="user-abc")
        fetched = db.get_booking(bid)
        assert fetched["user_id"] == "user-abc"

    def test_get_booking_returns_none_for_unknown_id(self):
        assert db.get_booking("nonexistent-id") is None

    def test_get_booking_scoped_to_user(self):
        bid = new_id()
        db.create_booking(bid, "dentist", "Boston", "today", {}, user_id="alice")
        # Correct user can retrieve
        assert db.get_booking(bid, user_id="alice") is not None
        # Other user gets None
        assert db.get_booking(bid, user_id="bob") is None

    def test_get_booking_no_user_filter(self):
        bid = new_id()
        db.create_booking(bid, "dentist", "Boston", "today", {}, user_id="alice")
        # Without user_id filter, returns the booking
        assert db.get_booking(bid) is not None

    def test_update_booking_status(self):
        bid = new_id()
        db.create_booking(bid, "doctor", "NYC", "this week", {})
        db.update_booking_status(bid, "completed")
        fetched = db.get_booking(bid)
        assert fetched["status"] == "completed"

    def test_update_booking_status_with_results(self):
        bid = new_id()
        db.create_booking(bid, "doctor", "NYC", "this week", {})
        results = [{"provider_name": "City Clinic", "call_status": "completed"}]
        db.update_booking_status(bid, "completed", results=results)
        fetched = db.get_booking(bid)
        assert fetched["status"] == "completed"
        assert len(fetched["results"]) == 1
        assert fetched["results"][0]["provider_name"] == "City Clinic"

    def test_update_booking_results(self):
        bid = new_id()
        db.create_booking(bid, "dentist", "Boston", "today", {})
        new_results = [{"provider_name": "Smile Co", "call_status": "pending"}]
        db.update_booking_results(bid, new_results)
        fetched = db.get_booking(bid)
        assert fetched["results"][0]["provider_name"] == "Smile Co"

    def test_get_all_bookings_returns_all(self):
        for _ in range(3):
            db.create_booking(new_id(), "doctor", "LA", "tomorrow", {})
        bookings = db.get_all_bookings()
        assert len(bookings) >= 3

    def test_get_all_bookings_user_scoped(self):
        db.create_booking(new_id(), "dentist", "Boston", "today", {}, user_id="alice")
        db.create_booking(new_id(), "dentist", "Boston", "today", {}, user_id="bob")
        alice_bookings = db.get_all_bookings(user_id="alice")
        assert all(b["user_id"] == "alice" for b in alice_bookings)

    def test_get_booking_by_conversation_id(self):
        bid = new_id()
        conv_id = "conv-" + new_id()
        db.create_booking(bid, "doctor", "Boston", "today", {})
        results = [{"conversation_id": conv_id, "call_status": "completed"}]
        db.update_booking_results(bid, results)
        # Only matches processing bookings; update status for match
        db.update_booking_status(bid, "processing", results=results)
        booking, idx = db.get_booking_by_conversation_id(conv_id)
        assert booking is not None
        assert idx == 0

    def test_get_booking_by_conversation_id_not_found(self):
        booking, idx = db.get_booking_by_conversation_id("nonexistent-conv-id")
        assert booking is None
        assert idx == -1

    def test_clear_all_bookings(self):
        db.create_booking(new_id(), "dentist", "Boston", "today", {})
        db.clear_all_bookings()
        assert db.get_all_bookings() == []

    def test_booking_preferences_round_trip(self):
        bid = new_id()
        prefs = {"rating_weight": 0.5, "preferred_time": "6 PM"}
        db.create_booking(bid, "dentist", "Boston", "today", prefs)
        fetched = db.get_booking(bid)
        assert fetched["preferences"]["preferred_time"] == "6 PM"
        assert fetched["preferences"]["rating_weight"] == 0.5


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

class TestTasks:
    def test_create_task_returns_dict_with_gathering_status(self):
        task = db.create_task(new_id())
        assert task["status"] == "gathering_info"
        assert task["extracted_data"] == {}
        assert task["conversation"] == []

    def test_create_task_stores_user_id(self):
        tid = new_id()
        db.create_task(tid, user_id="user-xyz")
        fetched = db.get_task(tid)
        assert fetched["user_id"] == "user-xyz"

    def test_get_task_returns_none_for_unknown(self):
        assert db.get_task("nonexistent") is None

    def test_get_task_scoped_to_user(self):
        tid = new_id()
        db.create_task(tid, user_id="alice")
        assert db.get_task(tid, user_id="alice") is not None
        assert db.get_task(tid, user_id="bob") is None

    def test_update_task_status(self):
        tid = new_id()
        db.create_task(tid, user_id="alice")
        db.update_task(tid, status="ready_to_call", user_id="alice")
        fetched = db.get_task(tid)
        assert fetched["status"] == "ready_to_call"

    def test_update_task_extracted_data(self):
        tid = new_id()
        db.create_task(tid, user_id="alice")
        data = {"service_type": "dentist", "location": "Boston"}
        db.update_task(tid, extracted_data=data, user_id="alice")
        fetched = db.get_task(tid)
        assert fetched["extracted_data"]["service_type"] == "dentist"

    def test_update_task_conversation(self):
        tid = new_id()
        db.create_task(tid, user_id="alice")
        convo = [{"role": "user", "content": "I need a dentist"}]
        db.update_task(tid, conversation=convo, user_id="alice")
        fetched = db.get_task(tid)
        assert fetched["conversation"][0]["content"] == "I need a dentist"

    def test_update_task_wrong_user_does_nothing(self):
        tid = new_id()
        db.create_task(tid, user_id="alice")
        db.update_task(tid, status="ready_to_call", user_id="bob")
        fetched = db.get_task(tid)
        # Status should remain unchanged
        assert fetched["status"] == "gathering_info"

    def test_get_all_tasks_user_scoped(self):
        db.create_task(new_id(), user_id="alice")
        db.create_task(new_id(), user_id="bob")
        alice_tasks = db.get_all_tasks(user_id="alice")
        assert all(t["user_id"] == "alice" for t in alice_tasks)


# ---------------------------------------------------------------------------
# Waitlist & Allowed Emails
# ---------------------------------------------------------------------------

class TestWaitlistAndAllowedEmails:
    def test_add_to_waitlist(self):
        result = db.add_to_waitlist("user@example.com", "Test User")
        assert result["email"] == "user@example.com"

    def test_waitlist_normalises_email_to_lowercase(self):
        db.add_to_waitlist("UPPER@EXAMPLE.COM", "Upper User")
        entries = db.get_waitlist()
        assert any(e["email"] == "upper@example.com" for e in entries)

    def test_get_waitlist_returns_added_entries(self):
        db.add_to_waitlist("a@test.com", "Alice")
        db.add_to_waitlist("b@test.com", "Bob")
        entries = db.get_waitlist()
        emails = [e["email"] for e in entries]
        assert "a@test.com" in emails
        assert "b@test.com" in emails

    def test_is_email_allowed_false_by_default(self):
        assert db.is_email_allowed("nobody@example.com") is False

    def test_is_email_allowed_empty_string(self):
        assert db.is_email_allowed("") is False

    def test_add_and_check_allowed_email(self):
        db.add_allowed_email("vip@example.com")
        assert db.is_email_allowed("vip@example.com") is True

    def test_allowed_email_case_insensitive(self):
        db.add_allowed_email("VIP@Example.com")
        assert db.is_email_allowed("vip@example.com") is True

    def test_get_allowed_emails_returns_added(self):
        db.add_allowed_email("admin@example.com")
        allowed = db.get_allowed_emails()
        assert any(e["email"] == "admin@example.com" for e in allowed)

    def test_duplicate_allowed_email_ignored(self):
        db.add_allowed_email("once@example.com")
        db.add_allowed_email("once@example.com")  # should not raise
        allowed = [e["email"] for e in db.get_allowed_emails()]
        assert allowed.count("once@example.com") == 1

    def test_clean_db_removes_bookings_and_tasks(self):
        db.create_booking(new_id(), "dentist", "Boston", "today", {})
        db.create_task(new_id())
        db.clean_db()
        assert db.get_all_bookings() == []
        assert db.get_all_tasks() == []
