#!/usr/bin/env python3
"""
Seed the database with two demo tasks for video recording.
Run from the backend directory: python seed_demo_tasks.py

Creates:
  1. Dentist in Cambridge, MA — completed with 2 provider results
  2. Veterinarian in Cambridge, MA — completed with 2 provider results
"""

import os
import sys
import uuid

# Run from backend directory so database module is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database as db

# Demo results that look good in the UI
DENTIST_RESULTS = [
    {
        "provider_id": "demo_dentist_1",
        "provider_name": "Cambridge Dental Associates",
        "phone": "+1 (617) 555-0101",
        "address": "1 Massachusetts Ave, Cambridge, MA 02139",
        "rating": 4.8,
        "distance": 0.5,
        "travel_time": 8,
        "availability_date": "Wednesday, February 12",
        "availability_time": "10:30 AM",
        "score": 92,
        "call_status": "completed",
        "has_availability": True,
    },
    {
        "provider_id": "demo_dentist_2",
        "provider_name": "Harvard Square Dental",
        "phone": "+1 (617) 555-0102",
        "address": "730 Massachusetts Ave, Cambridge, MA 02139",
        "rating": 4.5,
        "distance": 1.2,
        "travel_time": 12,
        "availability_date": "Thursday, February 13",
        "availability_time": "2:00 PM",
        "score": 85,
        "call_status": "completed",
        "has_availability": True,
    },
]

VET_RESULTS = [
    {
        "provider_id": "demo_vet_1",
        "provider_name": "Cambridge Veterinary Clinic",
        "phone": "+1 (617) 555-0201",
        "address": "874 Massachusetts Ave, Cambridge, MA 02139",
        "rating": 4.9,
        "distance": 0.8,
        "travel_time": 10,
        "availability_date": "Tuesday, February 11",
        "availability_time": "9:00 AM",
        "score": 95,
        "call_status": "completed",
        "has_availability": True,
    },
    {
        "provider_id": "demo_vet_2",
        "provider_name": "Harvard Square Animal Hospital",
        "phone": "+1 (617) 555-0202",
        "address": "2067 Massachusetts Ave, Cambridge, MA 02140",
        "rating": 4.6,
        "distance": 1.5,
        "travel_time": 14,
        "availability_date": "No availability",
        "availability_time": "-",
        "score": 0,
        "call_status": "completed",
        "has_availability": False,
    },
]


def main():
    db.init_db()

    # 1. Dentist booking
    dentist_id = str(uuid.uuid4())
    db.create_booking(
        booking_id=dentist_id,
        service_type="dentist",
        location="Cambridge, MA",
        timeframe="this week",
        preferences={"preferred_slots": "Tuesday or Wednesday morning"},
    )
    db.update_booking_status(dentist_id, "completed", DENTIST_RESULTS)
    print(f"✅ Demo task 1: dentist in Cambridge, MA (completed) — {dentist_id[:8]}...")

    # 2. Veterinarian booking
    vet_id = str(uuid.uuid4())
    db.create_booking(
        booking_id=vet_id,
        service_type="veterinarian",
        location="Cambridge, MA",
        timeframe="this week",
        preferences={},
    )
    db.update_booking_status(vet_id, "completed", VET_RESULTS)
    print(f"✅ Demo task 2: veterinarian in Cambridge, MA (completed) — {vet_id[:8]}...")

    print("\n🎬 Done. Open the dashboard Tasks page to see the two demo tasks.")


if __name__ == "__main__":
    main()
