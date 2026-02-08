"""
Simulated calendar availability for closing appointments in one call.
Generates concrete time windows from a timeframe so the outbound agent can propose specific slots.
"""
from datetime import datetime, timedelta
from typing import List


# Time windows we "see" on the user's calendar (simulated)
_AM = "9:00 AM–12:00 PM"
_AFTERNOON = "2:00–4:00 PM"
_LATE_AFTERNOON = "4:00–6:00 PM"


def get_simulated_availability(timeframe: str) -> List[str]:
    """
    Return a list of concrete availability slots for the given timeframe (simulated from "calendar").
    Used so the outbound agent can say e.g. "He's available Tuesday 2-4pm, Wednesday 9am-12pm — do you have anything then?"
    """
    if not (timeframe or "").strip():
        timeframe = "this week"
    tf = (timeframe or "this week").strip().lower().replace("_", " ")
    now = datetime.now()
    slots: List[str] = []

    if tf in ("today", "asap"):
        # Today: afternoon and late afternoon
        slots = [f"Today {_AFTERNOON}", f"Today {_LATE_AFTERNOON}"]
    elif tf == "tomorrow":
        d = now + timedelta(days=1)
        day = d.strftime("%A")
        slots = [f"{day} {_AM}", f"{day} {_AFTERNOON}"]
    elif tf == "this week":
        # Next 3–4 weekdays with mixed windows
        days_add = 0
        count = 0
        while count < 4 and days_add < 7:
            d = now + timedelta(days=days_add)
            days_add += 1
            if d.weekday() >= 5:  # skip weekend
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
        # Next week weekdays
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
        # Generic: use "this week" logic
        slots = get_simulated_availability("this week")

    return slots[:4]  # cap at 4 slots


def format_slots_for_agent(slots: List[str]) -> str:
    """Format slot list for use in agent first message and prompt."""
    if not slots:
        return "several times this week"
    if len(slots) == 1:
        return slots[0]
    return ", ".join(slots[:-1]) + ", or " + slots[-1]
