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

    # Bookings table (user_id for multi-tenant segregation)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            user_id TEXT,
            service_type TEXT NOT NULL,
            location TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at REAL NOT NULL,
            preferences TEXT,
            results TEXT
        )
    ''')
    _add_column_if_missing(cursor, 'bookings', 'user_id', 'TEXT')

    # Tasks table: each conversation is a task (user_id for multi-tenant segregation)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            user_id TEXT,
            status TEXT NOT NULL,
            extracted_data TEXT,
            conversation TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    ''')
    _add_column_if_missing(cursor, 'tasks', 'user_id', 'TEXT')

    # Waitlist: name, email, created_at (confirmation sent when email provider configured)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS waitlist (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at REAL NOT NULL,
            confirmation_sent_at REAL
        )
    ''')

    # Allowed emails: users you've added to the pool (can use Google sign-in when WAITLIST_MODE is on)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS allowed_emails (
            email TEXT PRIMARY KEY,
            added_at REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")


def _add_column_if_missing(cursor, table: str, column: str, col_type: str):
    """Add column to table if it doesn't exist (migration helper)."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

def create_booking(booking_id: str, service_type: str, location: str, timeframe: str, preferences: dict, user_id: Optional[str] = None) -> dict:
    """Create a new booking (optionally scoped to user_id)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    booking = {
        'booking_id': booking_id,
        'user_id': user_id,
        'service_type': service_type,
        'location': location,
        'timeframe': timeframe,
        'status': 'processing',
        'created_at': datetime.now().timestamp(),
        'preferences': json.dumps(preferences),
        'results': json.dumps([])
    }

    cursor.execute('''
        INSERT INTO bookings (booking_id, user_id, service_type, location, timeframe, status, created_at, preferences, results)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        booking['booking_id'],
        booking['user_id'],
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

def get_booking(booking_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    """Get a booking by ID. If user_id is provided, only return if booking belongs to that user (strict: no legacy NULL)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute('SELECT * FROM bookings WHERE booking_id = ? AND user_id = ?', (booking_id, user_id))
    else:
        cursor.execute('SELECT * FROM bookings WHERE booking_id = ?', (booking_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    # Row: booking_id, user_id, service_type, location, timeframe, status, created_at, preferences, results
    return _row_to_booking(row)


def _row_to_booking(row) -> dict:
    """Map DB row to booking dict (handles both 8 and 9 column schemas)."""
    if len(row) >= 9:
        return {
            'booking_id': row[0],
            'user_id': row[1],
            'service_type': row[2],
            'location': row[3],
            'timeframe': row[4],
            'status': row[5],
            'created_at': row[6],
            'preferences': json.loads(row[7]) if row[7] else {},
            'results': json.loads(row[8]) if row[8] else []
        }
    # Legacy 8-column row (no user_id)
    return {
        'booking_id': row[0],
        'user_id': None,
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

def get_booking_by_conversation_id(conversation_id: str) -> Optional[tuple]:
    """
    Find a processing booking that has a result with this conversation_id.
    Returns (booking_dict, result_index) or (None, -1). Used by webhooks (no user filter).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bookings WHERE status = ? ORDER BY created_at DESC', ('processing',))
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        booking = _row_to_booking(row)
        results = booking.get('results') or []
        for idx, r in enumerate(results):
            if (r.get('conversation_id') or r.get('call_sid')) == conversation_id:
                return booking, idx
    return None, -1


def get_all_bookings(user_id: Optional[str] = None) -> List[dict]:
    """Get all bookings sorted by creation time. If user_id is provided, only return that user's bookings."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute('SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    else:
        cursor.execute('SELECT * FROM bookings ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_booking(row) for row in rows]

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

def create_task(task_id: str, user_id: Optional[str] = None) -> dict:
    """Create a new task in gathering_info status (optionally scoped to user_id)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().timestamp()
    cursor.execute('''
        INSERT INTO tasks (task_id, user_id, status, extracted_data, conversation, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (task_id, user_id, 'gathering_info', json.dumps({}), json.dumps([]), now, now))
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


def _row_to_task(row) -> dict:
    """Map DB row to task dict (handles both 6 and 7 column schemas)."""
    if len(row) >= 7:
        return {
            'task_id': row[0],
            'user_id': row[1],
            'status': row[2],
            'extracted_data': json.loads(row[3]) if row[3] else {},
            'conversation': json.loads(row[4]) if row[4] else [],
            'created_at': row[5],
            'updated_at': row[6],
        }
    return {
        'task_id': row[0],
        'user_id': None,
        'status': row[1],
        'extracted_data': json.loads(row[2]) if row[2] else {},
        'conversation': json.loads(row[3]) if row[3] else [],
        'created_at': row[4],
        'updated_at': row[5],
    }


def get_task(task_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    """Get a task by ID. If user_id is provided, only return if task belongs to that user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute('SELECT * FROM tasks WHERE task_id = ? AND user_id = ?', (task_id, user_id))
    else:
        cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_task(row)


def update_task(task_id: str, status: str = None, extracted_data: dict = None, conversation: list = None, user_id: Optional[str] = None):
    """Update task fields. If user_id is provided, only update if task belongs to that user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().timestamp()
    task = get_task(task_id, user_id)
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


def get_all_tasks(user_id: Optional[str] = None) -> List[dict]:
    """Get all tasks sorted by updated_at desc. If user_id is provided, only return that user's tasks."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY updated_at DESC', (user_id,))
    else:
        cursor.execute('SELECT * FROM tasks ORDER BY updated_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_task(row) for row in rows]


# --- Waitlist and allowed emails (dev / gated signup) ---

def add_to_waitlist(email: str, name: str, confirmation_sent: bool = False) -> dict:
    """Add or update waitlist signup. Returns the row."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().timestamp()
    cursor.execute('''
        INSERT INTO waitlist (email, name, created_at, confirmation_sent_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET name = ?, confirmation_sent_at = ?
    ''', (email.strip().lower(), (name or '').strip(), now, now if confirmation_sent else None, (name or '').strip(), now if confirmation_sent else None))
    conn.commit()
    conn.close()
    return {'email': email.strip().lower(), 'name': (name or '').strip(), 'created_at': now}


def get_waitlist() -> List[dict]:
    """List all waitlist signups, newest first."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT email, name, created_at, confirmation_sent_at FROM waitlist ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [{'email': r[0], 'name': r[1], 'created_at': r[2], 'confirmation_sent_at': r[3]} for r in rows]


def set_confirmation_sent(email: str):
    """Mark confirmation email as sent."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE waitlist SET confirmation_sent_at = ? WHERE email = ?', (datetime.now().timestamp(), email.strip().lower()))
    conn.commit()
    conn.close()


def is_email_allowed(email: str) -> bool:
    """True if email is in the allowed user pool."""
    if not email:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM allowed_emails WHERE email = ?', (email.strip().lower(),))
    found = cursor.fetchone() is not None
    conn.close()
    return found


def add_allowed_email(email: str) -> dict:
    """Add email to the allowed pool. Returns the row."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().timestamp()
    cursor.execute('INSERT OR IGNORE INTO allowed_emails (email, added_at) VALUES (?, ?)', (email.strip().lower(), now))
    conn.commit()
    conn.close()
    return {'email': email.strip().lower(), 'added_at': now}


def get_allowed_emails() -> List[dict]:
    """List all allowed emails."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT email, added_at FROM allowed_emails ORDER BY added_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [{'email': r[0], 'added_at': r[1]} for r in rows]
