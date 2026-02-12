"""
Firestore Database for CallPilot
Stores bookings, tasks, waitlist, and allowed emails with persistence across deploys.
Falls back to SQLite if GOOGLE_CLOUD_PROJECT is not set (local dev without GCP).
"""

import json
import os
from datetime import datetime
from typing import Optional, List

# ---------------------------------------------------------------------------
# Firestore client (initialised lazily so import never fails)
# ---------------------------------------------------------------------------

_firestore_db = None
_USE_FIRESTORE: Optional[bool] = None


def _use_firestore() -> bool:
    """Return True if we should use Firestore, False for SQLite fallback."""
    global _USE_FIRESTORE
    if _USE_FIRESTORE is not None:
        return _USE_FIRESTORE
    # Explicit opt-out via env (e.g. USE_SQLITE=true for local dev)
    if os.getenv('USE_SQLITE', '').lower() in ('1', 'true', 'yes'):
        _USE_FIRESTORE = False
        return False
    # If a GCP project is detectable, use Firestore
    project = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCLOUD_PROJECT') or os.getenv('GCP_PROJECT')
    if project:
        _USE_FIRESTORE = True
        return True
    # Try to detect from Application Default Credentials
    try:
        import google.auth
        _, detected = google.auth.default()
        _USE_FIRESTORE = detected is not None
    except Exception:
        _USE_FIRESTORE = False
    return _USE_FIRESTORE


def _get_fs():
    """Return the Firestore client (lazy init)."""
    global _firestore_db
    if _firestore_db is None:
        from google.cloud import firestore
        _firestore_db = firestore.Client()
    return _firestore_db


# ---------------------------------------------------------------------------
# SQLite fallback (for local dev without GCP)
# ---------------------------------------------------------------------------
import sqlite3

_SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'callpilot.db')


def _sqlite_conn():
    return sqlite3.connect(_SQLITE_PATH)


def _add_column_if_missing(cursor, table: str, column: str, col_type: str):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

def init_db():
    if _use_firestore():
        print("✅ Using Firestore for persistent storage")
        return

    # SQLite fallback
    conn = _sqlite_conn()
    cursor = conn.cursor()
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS waitlist (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at REAL NOT NULL,
            confirmation_sent_at REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS allowed_emails (
            email TEXT PRIMARY KEY,
            added_at REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {_SQLITE_PATH} (SQLite fallback)")


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

def create_booking(booking_id: str, service_type: str, location: str, timeframe: str, preferences: dict, user_id: Optional[str] = None) -> dict:
    now = datetime.now().timestamp()
    booking = {
        'booking_id': booking_id,
        'user_id': user_id,
        'service_type': service_type,
        'location': location,
        'timeframe': timeframe,
        'status': 'processing',
        'created_at': now,
        'preferences': preferences,
        'results': [],
    }

    if _use_firestore():
        _get_fs().collection('bookings').document(booking_id).set(booking)
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bookings (booking_id, user_id, service_type, location, timeframe, status, created_at, preferences, results)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (booking_id, user_id, service_type, location, timeframe, 'processing', now, json.dumps(preferences), json.dumps([])))
        conn.commit()
        conn.close()

    return booking


def get_booking(booking_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    if _use_firestore():
        doc = _get_fs().collection('bookings').document(booking_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if user_id is not None and data.get('user_id') != user_id:
            return None
        return data
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        if user_id is not None:
            cursor.execute('SELECT * FROM bookings WHERE booking_id = ? AND user_id = ?', (booking_id, user_id))
        else:
            cursor.execute('SELECT * FROM bookings WHERE booking_id = ?', (booking_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return _row_to_booking(row)


def _row_to_booking(row) -> dict:
    if len(row) >= 9:
        return {
            'booking_id': row[0], 'user_id': row[1], 'service_type': row[2], 'location': row[3],
            'timeframe': row[4], 'status': row[5], 'created_at': row[6],
            'preferences': json.loads(row[7]) if row[7] else {},
            'results': json.loads(row[8]) if row[8] else [],
        }
    return {
        'booking_id': row[0], 'user_id': None, 'service_type': row[1], 'location': row[2],
        'timeframe': row[3], 'status': row[4], 'created_at': row[5],
        'preferences': json.loads(row[6]) if row[6] else {},
        'results': json.loads(row[7]) if row[7] else [],
    }


def update_booking_status(booking_id: str, status: str, results: Optional[List[dict]] = None):
    if _use_firestore():
        update = {'status': status}
        if results is not None:
            update['results'] = results
        _get_fs().collection('bookings').document(booking_id).update(update)
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        if results is not None:
            cursor.execute('UPDATE bookings SET status = ?, results = ? WHERE booking_id = ?',
                           (status, json.dumps(results), booking_id))
        else:
            cursor.execute('UPDATE bookings SET status = ? WHERE booking_id = ?', (status, booking_id))
        conn.commit()
        conn.close()


def update_booking_results(booking_id: str, results: List[dict]):
    if _use_firestore():
        _get_fs().collection('bookings').document(booking_id).update({'results': results})
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('UPDATE bookings SET results = ? WHERE booking_id = ?', (json.dumps(results), booking_id))
        conn.commit()
        conn.close()


def get_booking_by_conversation_id(conversation_id: str) -> Optional[tuple]:
    """Find a processing booking that has a result with this conversation_id. Used by webhooks (no user filter)."""
    if _use_firestore():
        docs = _get_fs().collection('bookings').where('status', '==', 'processing').order_by('created_at', direction='DESCENDING').stream()
        for doc in docs:
            booking = doc.to_dict()
            results = booking.get('results') or []
            for idx, r in enumerate(results):
                if (r.get('conversation_id') or r.get('call_sid')) == conversation_id:
                    return booking, idx
        return None, -1
    else:
        conn = _sqlite_conn()
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
    if _use_firestore():
        coll = _get_fs().collection('bookings')
        if user_id is not None:
            query = coll.where('user_id', '==', user_id).order_by('created_at', direction='DESCENDING')
        else:
            query = coll.order_by('created_at', direction='DESCENDING')
        return [doc.to_dict() for doc in query.stream()]
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        if user_id is not None:
            cursor.execute('SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        else:
            cursor.execute('SELECT * FROM bookings ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [_row_to_booking(row) for row in rows]


def clear_all_bookings():
    if _use_firestore():
        _delete_collection('bookings')
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bookings')
        conn.commit()
        conn.close()
    print("🗑️  All bookings cleared")


def clean_db():
    if _use_firestore():
        _delete_collection('bookings')
        _delete_collection('tasks')
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bookings')
        cursor.execute('DELETE FROM tasks')
        conn.commit()
        conn.close()
    print("🗑️  Database cleaned (bookings and tasks)")


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def create_task(task_id: str, user_id: Optional[str] = None) -> dict:
    now = datetime.now().timestamp()
    task = {
        'task_id': task_id,
        'user_id': user_id,
        'status': 'gathering_info',
        'extracted_data': {},
        'conversation': [],
        'created_at': now,
        'updated_at': now,
    }
    if _use_firestore():
        _get_fs().collection('tasks').document(task_id).set(task)
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (task_id, user_id, status, extracted_data, conversation, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (task_id, user_id, 'gathering_info', json.dumps({}), json.dumps([]), now, now))
        conn.commit()
        conn.close()
    return task


def _row_to_task(row) -> dict:
    if len(row) >= 7:
        return {
            'task_id': row[0], 'user_id': row[1], 'status': row[2],
            'extracted_data': json.loads(row[3]) if row[3] else {},
            'conversation': json.loads(row[4]) if row[4] else [],
            'created_at': row[5], 'updated_at': row[6],
        }
    return {
        'task_id': row[0], 'user_id': None, 'status': row[1],
        'extracted_data': json.loads(row[2]) if row[2] else {},
        'conversation': json.loads(row[3]) if row[3] else [],
        'created_at': row[4], 'updated_at': row[5],
    }


def get_task(task_id: str, user_id: Optional[str] = None) -> Optional[dict]:
    if _use_firestore():
        doc = _get_fs().collection('tasks').document(task_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if user_id is not None and data.get('user_id') != user_id:
            return None
        return data
    else:
        conn = _sqlite_conn()
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
    now = datetime.now().timestamp()

    if _use_firestore():
        doc_ref = _get_fs().collection('tasks').document(task_id)
        doc = doc_ref.get()
        if not doc.exists:
            return
        data = doc.to_dict()
        if user_id is not None and data.get('user_id') != user_id:
            return
        update = {'updated_at': now}
        if status is not None:
            update['status'] = status
        if extracted_data is not None:
            update['extracted_data'] = extracted_data
        if conversation is not None:
            update['conversation'] = conversation
        doc_ref.update(update)
    else:
        task = get_task(task_id, user_id)
        if not task:
            return
        if status is not None:
            task['status'] = status
        if extracted_data is not None:
            task['extracted_data'] = extracted_data
        if conversation is not None:
            task['conversation'] = conversation
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks SET status = ?, extracted_data = ?, conversation = ?, updated_at = ?
            WHERE task_id = ?
        ''', (task['status'], json.dumps(task['extracted_data']), json.dumps(task['conversation']), now, task_id))
        conn.commit()
        conn.close()


def get_all_tasks(user_id: Optional[str] = None) -> List[dict]:
    if _use_firestore():
        coll = _get_fs().collection('tasks')
        if user_id is not None:
            query = coll.where('user_id', '==', user_id).order_by('updated_at', direction='DESCENDING')
        else:
            query = coll.order_by('updated_at', direction='DESCENDING')
        return [doc.to_dict() for doc in query.stream()]
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        if user_id is not None:
            cursor.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY updated_at DESC', (user_id,))
        else:
            cursor.execute('SELECT * FROM tasks ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [_row_to_task(row) for row in rows]


# ---------------------------------------------------------------------------
# Waitlist and allowed emails
# ---------------------------------------------------------------------------

def add_to_waitlist(email: str, name: str, confirmation_sent: bool = False) -> dict:
    email_key = email.strip().lower()
    name_clean = (name or '').strip()
    now = datetime.now().timestamp()

    if _use_firestore():
        _get_fs().collection('waitlist').document(email_key).set({
            'email': email_key,
            'name': name_clean,
            'created_at': now,
            'confirmation_sent_at': now if confirmation_sent else None,
        }, merge=True)
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO waitlist (email, name, created_at, confirmation_sent_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET name = ?, confirmation_sent_at = ?
        ''', (email_key, name_clean, now, now if confirmation_sent else None, name_clean, now if confirmation_sent else None))
        conn.commit()
        conn.close()

    return {'email': email_key, 'name': name_clean, 'created_at': now}


def get_waitlist() -> List[dict]:
    if _use_firestore():
        docs = _get_fs().collection('waitlist').order_by('created_at', direction='DESCENDING').stream()
        return [doc.to_dict() for doc in docs]
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT email, name, created_at, confirmation_sent_at FROM waitlist ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [{'email': r[0], 'name': r[1], 'created_at': r[2], 'confirmation_sent_at': r[3]} for r in rows]


def set_confirmation_sent(email: str):
    email_key = email.strip().lower()
    now = datetime.now().timestamp()
    if _use_firestore():
        _get_fs().collection('waitlist').document(email_key).update({'confirmation_sent_at': now})
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('UPDATE waitlist SET confirmation_sent_at = ? WHERE email = ?', (now, email_key))
        conn.commit()
        conn.close()


def is_email_allowed(email: str) -> bool:
    if not email:
        return False
    email_key = email.strip().lower()
    if _use_firestore():
        doc = _get_fs().collection('allowed_emails').document(email_key).get()
        return doc.exists
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM allowed_emails WHERE email = ?', (email_key,))
        found = cursor.fetchone() is not None
        conn.close()
        return found


def add_allowed_email(email: str) -> dict:
    email_key = email.strip().lower()
    now = datetime.now().timestamp()
    if _use_firestore():
        _get_fs().collection('allowed_emails').document(email_key).set({'email': email_key, 'added_at': now})
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO allowed_emails (email, added_at) VALUES (?, ?)', (email_key, now))
        conn.commit()
        conn.close()
    return {'email': email_key, 'added_at': now}


def get_allowed_emails() -> List[dict]:
    if _use_firestore():
        docs = _get_fs().collection('allowed_emails').order_by('added_at', direction='DESCENDING').stream()
        return [doc.to_dict() for doc in docs]
    else:
        conn = _sqlite_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT email, added_at FROM allowed_emails ORDER BY added_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [{'email': r[0], 'added_at': r[1]} for r in rows]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _delete_collection(name: str, batch_size: int = 100):
    """Delete all documents in a Firestore collection."""
    coll = _get_fs().collection(name)
    while True:
        docs = list(coll.limit(batch_size).stream())
        if not docs:
            break
        batch = _get_fs().batch()
        for doc in docs:
            batch.delete(doc.reference)
        batch.commit()
