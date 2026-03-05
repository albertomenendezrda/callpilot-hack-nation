"""
Tests for backend/availability.py

Covers:
  - _parse_preferred_time: various time phrase formats
  - get_simulated_availability: slot generation per timeframe
  - format_slots_for_agent: human-readable slot formatting
"""

from datetime import datetime, timedelta

import pytest

from availability import (
    _parse_preferred_time,
    format_slots_for_agent,
    get_simulated_availability,
)


# ---------------------------------------------------------------------------
# _parse_preferred_time
# ---------------------------------------------------------------------------

class TestParsePreferredTime:
    def test_none_input(self):
        assert _parse_preferred_time(None) is None  # type: ignore[arg-type]

    def test_empty_string(self):
        assert _parse_preferred_time("") is None

    def test_whitespace_only(self):
        assert _parse_preferred_time("   ") is None

    def test_noon(self):
        assert _parse_preferred_time("noon") == "12:00 PM"

    def test_noon_with_qualifier(self):
        assert _parse_preferred_time("12 noon") == "12:00 PM"

    def test_12pm_no_space(self):
        assert _parse_preferred_time("12pm") == "12:00 PM"

    def test_12pm_with_space(self):
        assert _parse_preferred_time("12 pm") == "12:00 PM"

    def test_evening(self):
        assert _parse_preferred_time("evening") == "evening (e.g. 6–8 PM)"

    def test_dinner_time(self):
        assert _parse_preferred_time("dinner time") == "evening (e.g. 6–8 PM)"

    def test_6pm_uppercase(self):
        assert _parse_preferred_time("6 PM") == "6:00 PM"

    def test_6pm_lowercase(self):
        assert _parse_preferred_time("6pm") == "6:00 PM"

    def test_6am(self):
        assert _parse_preferred_time("6 AM") == "6:00 AM"

    def test_9am(self):
        assert _parse_preferred_time("9am") == "9:00 AM"

    def test_12am_midnight(self):
        # 12 AM should be midnight (hour 0)
        result = _parse_preferred_time("12 AM")
        assert result == "12:00 AM"

    def test_730pm(self):
        assert _parse_preferred_time("7:30 PM") == "7:30 PM"

    def test_1045am(self):
        assert _parse_preferred_time("10:45 AM") == "10:45 AM"

    def test_no_period_defaults_to_pm(self):
        # If no AM/PM given, implementation defaults to PM
        result = _parse_preferred_time("6")
        assert result == "6:00 PM"


# ---------------------------------------------------------------------------
# get_simulated_availability
# ---------------------------------------------------------------------------

class TestGetSimulatedAvailability:
    def test_returns_at_most_4_slots(self):
        slots = get_simulated_availability("this week")
        assert len(slots) <= 4

    def test_today_returns_2_slots(self):
        slots = get_simulated_availability("today")
        assert len(slots) == 2

    def test_today_slots_start_with_today(self):
        slots = get_simulated_availability("today")
        for slot in slots:
            assert slot.startswith("Today")

    def test_asap_treated_as_today(self):
        slots_today = get_simulated_availability("today")
        slots_asap = get_simulated_availability("asap")
        assert slots_today == slots_asap

    def test_today_with_preferred_time(self):
        slots = get_simulated_availability("today", preferred_time="6 PM")
        assert any("6:00 PM" in s for s in slots)

    def test_tomorrow_returns_2_slots(self):
        slots = get_simulated_availability("tomorrow")
        assert len(slots) == 2

    def test_tomorrow_slots_contain_weekday(self):
        tomorrow = datetime.now() + timedelta(days=1)
        expected_day = tomorrow.strftime("%A")
        slots = get_simulated_availability("tomorrow")
        for slot in slots:
            assert expected_day in slot

    def test_tomorrow_with_preferred_time(self):
        slots = get_simulated_availability("tomorrow", preferred_time="9 AM")
        assert any("9:00 AM" in s for s in slots)

    def test_this_week_returns_weekday_slots(self):
        slots = get_simulated_availability("this week")
        # All slots should contain a weekday name (or be today)
        weekdays = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                    "Saturday", "Sunday"}  # allow all for boundary cases
        for slot in slots:
            first_word = slot.split()[0]
            assert first_word in weekdays

    def test_this_week_with_preferred_time_includes_time(self):
        slots = get_simulated_availability("this week", preferred_time="3 PM")
        assert any("3:00 PM" in s for s in slots)

    def test_next_week_returns_4_slots(self):
        slots = get_simulated_availability("next week")
        assert len(slots) == 4

    def test_next_week_starts_on_monday(self):
        slots = get_simulated_availability("next week")
        assert slots[0].startswith("Monday")

    def test_next_week_with_preferred_time(self):
        slots = get_simulated_availability("next week", preferred_time="noon")
        assert all("12:00 PM" in s for s in slots)

    def test_empty_timeframe_defaults_gracefully(self):
        slots = get_simulated_availability("")
        assert len(slots) > 0

    def test_none_timeframe_defaults_gracefully(self):
        slots = get_simulated_availability(None)  # type: ignore[arg-type]
        assert len(slots) > 0

    def test_unknown_timeframe_falls_back_to_this_week(self):
        # An arbitrary/unknown string should fall back to "this week" logic
        slots_unknown = get_simulated_availability("next quarter")
        slots_week = get_simulated_availability("this week")
        assert len(slots_unknown) == len(slots_week)

    def test_month_timeframe_returns_weekday_slots(self):
        slots = get_simulated_availability("this month")
        assert len(slots) >= 1

    def test_underscore_normalised(self):
        # "this_week" should work the same as "this week"
        slots = get_simulated_availability("this_week")
        assert len(slots) == len(get_simulated_availability("this week"))


# ---------------------------------------------------------------------------
# format_slots_for_agent
# ---------------------------------------------------------------------------

class TestFormatSlotsForAgent:
    def test_empty_list(self):
        assert format_slots_for_agent([]) == "several times this week"

    def test_single_slot(self):
        assert format_slots_for_agent(["Monday 2:00–4:00 PM"]) == "Monday 2:00–4:00 PM"

    def test_two_slots(self):
        result = format_slots_for_agent(["Monday 9 AM", "Tuesday 2 PM"])
        assert result == "Monday 9 AM, or Tuesday 2 PM"

    def test_three_slots_uses_oxford_or(self):
        result = format_slots_for_agent(["Mon", "Tue", "Wed"])
        assert result == "Mon, Tue, or Wed"

    def test_four_slots(self):
        result = format_slots_for_agent(["A", "B", "C", "D"])
        assert result == "A, B, C, or D"
