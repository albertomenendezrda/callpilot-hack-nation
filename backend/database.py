"""
SQLite Database for CallPilot
Stores bookings and results with persistence
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'callpilot.db')

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            service_type TEXT NOT NULL,
            location TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at REAL NOT NULL,
            preferences TEXT,
            results TEXT
        )
    ''')

    # Tasks table: each conversation is a task (gathering_info -> ready_to_call | requires_user_attention)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            extracted_data TEXT,
            conversation TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")

def create_booking(booking_id: str, service_type: str, location: str, timeframe: str, preferences: dict) -> dict:
    """Create a new booking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    booking = {
        'booking_id': booking_id,
        'service_type': service_type,
        'location': location,
        'timeframe': timeframe,
        'status': 'processing',
        'created_at': datetime.now().timestamp(),
        'preferences': json.dumps(preferences),
        'results': json.dumps([])
    }

    cursor.execute('''
        INSERT INTO bookings (booking_id, service_type, location, timeframe, status, created_at, preferences, results)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        booking['booking_id'],
        booking['service_type'],
        booking['location'],
        booking['timeframe'],
        booking['status'],
        booking['created_at'],
        booking['preferences'],
        booking['results']
    ))

    conn.commit()
    conn.close()

    return booking

def get_booking(booking_id: str) -> Optional[dict]:
    """Get a booking by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM bookings WHERE booking_id = ?', (booking_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        'booking_id': row[0],
        'service_type': row[1],
        'location': row[2],
        'timeframe': row[3],
        'status': row[4],
        'created_at': row[5],
        'preferences': json.loads(row[6]) if row[6] else {},
        'results': json.loads(row[7]) if row[7] else []
    }

def update_booking_status(booking_id: str, status: str, results: Optional[List[dict]] = None):
    """Update booking status and results"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if results is not None:
        cursor.execute('''
            UPDATE bookings
            SET status = ?, results = ?
            WHERE booking_id = ?
        ''', (status, json.dumps(results), booking_id))
    else:
        cursor.execute('''
            UPDATE bookings
            SET status = ?
            WHERE booking_id = ?
        ''', (status, booking_id))

    conn.commit()
    conn.close()

def update_booking_results(booking_id: str, results: List[dict]):
    """Update booking results without changing status (for progressive updates)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE bookings
        SET results = ?
        WHERE booking_id = ?
    ''', (json.dumps(results), booking_id))

    conn.commit()
    conn.close()

def get_all_bookings() -> List[dict]:
    """Get all bookings sorted by creation time"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM bookings ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()

    bookings = []
    for row in rows:
        bookings.append({
            'booking_id': row[0],
            'service_type': row[1],
            'location': row[2],
            'timeframe': row[3],
            'status': row[4],
            'created_at': row[5],
            'preferences': json.loads(row[6]) if row[6] else {},
            'results': json.loads(row[7]) if row[7] else []
        })

    return bookings

def clear_all_bookings():
    """Clear all bookings (for testing)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bookings')
    conn.commit()
    conn.close()
    print("🗑️  All bookings cleared")


def clean_db():
    """Clear all data from bookings and tasks tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bookings')
    cursor.execute('DELETE FROM tasks')
    conn.commit()
    conn.close()
    print("🗑️  Database cleaned (bookings and tasks)")


# --- Tasks (conversation-based info gathering) ---

def create_task(task_id: str) -> dict:
    """Create a new task in gathering_info status."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().timestamp()
    cursor.execute('''
        INSERT INTO tasks (task_id, status, extracted_data, conversation, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (task_id, 'gathering_info', json.dumps({}), json.dumps([]), now, now))
    conn.commit()
    conn.close()
    return {
        'task_id': task_id,
        'status': 'gathering_info',
        'extracted_data': {},
        'conversation': [],
        'created_at': now,
        'updated_at': now,
    }


def get_task(task_id: str) -> Optional[dict]:
    """Get a task by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        'task_id': row[0],
        'status': row[1],
        'extracted_data': json.loads(row[2]) if row[2] else {},
        'conversation': json.loads(row[3]) if row[3] else [],
        'created_at': row[4],
        'updated_at': row[5],
    }


def update_task(task_id: str, status: str = None, extracted_data: dict = None, conversation: list = None):
    """Update task fields."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().timestamp()
    task = get_task(task_id)
    if not task:
        conn.close()
        return
    if status is not None:
        task['status'] = status
    if extracted_data is not None:
        task['extracted_data'] = extracted_data
    if conversation is not None:
        task['conversation'] = conversation
    task['updated_at'] = now
    cursor.execute('''
        UPDATE tasks SET status = ?, extracted_data = ?, conversation = ?, updated_at = ?
        WHERE task_id = ?
    ''', (task['status'], json.dumps(task['extracted_data']), json.dumps(task['conversation']), now, task_id))
    conn.commit()
    conn.close()


def get_all_tasks() -> List[dict]:
    """Get all tasks sorted by updated_at desc."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks ORDER BY updated_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [{
        'task_id': row[0],
        'status': row[1],
        'extracted_data': json.loads(row[2]) if row[2] else {},
        'conversation': json.loads(row[3]) if row[3] else [],
        'created_at': row[4],
        'updated_at': row[5],
    } for row in rows]
