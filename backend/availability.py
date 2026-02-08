"""
Simulated calendar availability for closing appointments in one call.
Generates concrete time windows from a timeframe so the outbound agent can propose specific slots.
When the user states a specific time (e.g. "tomorrow at 6 PM"), we use that instead of generic windows.
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional


# Time windows we "see" on the user's calendar (simulated)
_AM = "9:00 AM–12:00 PM"
_AFTERNOON = "2:00–4:00 PM"
_LATE_AFTERNOON = "4:00–6:00 PM"


def _parse_preferred_time(preferred_time: str) -> Optional[str]:
    """
    Parse user phrase like "6 PM", "6pm", "noon", "7:30 PM", "evening" into a display time for the slot.
    Returns e.g. "6:00 PM", "12:00 PM", "7:30 PM", "evening", or None if unparseable.
    """
    if not (preferred_time or "").strip():
        return None
    s = preferred_time.strip().lower()
    # noon / 12
    if s in ("noon", "12 noon", "12pm", "12 pm"):
        return "12:00 PM"
    if s in ("evening", "dinner time"):
        return "evening (e.g. 6–8 PM)"
    # 6 PM, 6pm, 7:30 PM
    m = re.match(r"(\d{1,2})(?:\s*:\s*(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?", s)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        period = (m.group(3) or "pm").replace(".", "").lower()
        if period == "am" and hour == 12:
            hour = 0
        elif period == "pm" and hour != 12:
            hour += 12
        if minute > 0:
            return f"{hour % 12 or 12}:{minute:02d} {'PM' if hour >= 12 else 'AM'}"
        return f"{hour % 12 or 12}:00 {'PM' if hour >= 12 else 'AM'}"
    return preferred_time.strip() if len(s) <= 20 else None


def get_simulated_availability(timeframe: str, preferred_time: Optional[str] = None) -> List[str]:
    """
    Return a list of concrete availability slots (simulated from "calendar").
    If the user stated a specific time (e.g. "6 PM"), preferred_time should be set so we return slots that match.
    """
    if not (timeframe or "").strip():
        timeframe = "this week"
    tf = (timeframe or "this week").strip().lower().replace("_", " ")
    now = datetime.now()
    slots: List[str] = []
    parsed_time = _parse_preferred_time(preferred_time) if preferred_time else None

    if tf in ("today", "asap"):
        if parsed_time:
            slots = [f"Today {parsed_time}", f"Today around that time"]
        else:
            slots = [f"Today {_AFTERNOON}", f"Today {_LATE_AFTERNOON}"]
    elif tf == "tomorrow":
        d = now + timedelta(days=1)
        day = d.strftime("%A")
        if parsed_time:
            slots = [f"{day} {parsed_time}", f"{day} around that time"]
        else:
            slots = [f"{day} {_AM}", f"{day} {_AFTERNOON}"]
    elif tf == "this week":
        if parsed_time:
            # User said e.g. "this week at 6 PM" — use that time on next few weekdays
            days_add = 0
            count = 0
            while count < 4 and days_add < 7:
                d = now + timedelta(days=days_add)
                days_add += 1
                if d.weekday() >= 5:
                    continue
                day = d.strftime("%A")
                slots.append(f"{day} {parsed_time}")
                count += 1
        else:
            # Next 3–4 weekdays with mixed windows
            days_add = 0
            count = 0
            while count < 4 and days_add < 7:
                d = now + timedelta(days=days_add)
                days_add += 1
                if d.weekday() >= 5:
                    continue
                day = d.strftime("%A")
                if count == 0:
                    slots.append(f"{day} {_AFTERNOON}")
                elif count == 1:
                    slots.append(f"{day} {_AM}")
                elif count == 2:
                    slots.append(f"{day} {_AFTERNOON}")
                else:
                    slots.append(f"{day} morning or afternoon")
                count += 1
    elif tf == "next week":
        if parsed_time:
            next_monday = now + timedelta(days=(7 - now.weekday()))
            for i in range(4):
                d = next_monday + timedelta(days=i)
                day = d.strftime("%A")
                slots.append(f"{day} {parsed_time}")
        else:
            next_monday = now + timedelta(days=(7 - now.weekday()))
            for i in range(4):
                d = next_monday + timedelta(days=i)
                day = d.strftime("%A")
                if i % 2 == 0:
                    slots.append(f"{day} {_AM}")
                else:
                    slots.append(f"{day} {_AFTERNOON}")
    elif "month" in tf:
        # This month: spread over next two weeks
        for i in range(1, 8, 2):
            d = now + timedelta(days=i)
            if d.weekday() >= 5:
                continue
            day = d.strftime("%A, %b %d")
            slots.append(f"{day} {_AFTERNOON}")
            if len(slots) >= 4:
                break
    else:
        # Generic: use "this week" logic (without preferred_time to avoid wrong day)
        slots = get_simulated_availability("this week", preferred_time=None)

    return slots[:4]  # cap at 4 slots


def format_slots_for_agent(slots: List[str]) -> str:
    """Format slot list for use in agent first message and prompt."""
    if not slots:
        return "several times this week"
    if len(slots) == 1:
        return slots[0]
    return ", ".join(slots[:-1]) + ", or " + slots[-1]
