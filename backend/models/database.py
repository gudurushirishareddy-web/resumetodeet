"""
Database Models - SQLite with direct SQL (no ORM dependency)
"""
import sqlite3
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def get_db_path():
    return os.environ.get('DATABASE_PATH',
        os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'deet.db'))


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize database schema."""
    os.makedirs(os.path.dirname(get_db_path()), exist_ok=True)
    conn = get_connection()
    c = conn.cursor()

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # Resumes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            extracted_data TEXT,
            quality_score REAL DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # DEET registrations table
    c.execute('''
        CREATE TABLE IF NOT EXISTS deet_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resume_id INTEGER,
            registration_data TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            submitted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (resume_id) REFERENCES resumes(id)
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


# ---- User operations ----

def create_user(full_name, email, password_hash):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            'INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)',
            (full_name, email, password_hash)
        )
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_connection()
    c = conn.cursor()
    row = c.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id):
    conn = get_connection()
    c = conn.cursor()
    row = c.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_last_login(user_id):
    conn = get_connection()
    conn.execute('UPDATE users SET last_login = ? WHERE id = ?',
                 (datetime.utcnow(), user_id))
    conn.commit()
    conn.close()


# ---- Resume operations ----

def save_resume(user_id, filename, file_path, file_type, extracted_data, quality_score):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        '''INSERT INTO resumes (user_id, filename, file_path, file_type, extracted_data, quality_score)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (user_id, filename, file_path, file_type,
         json.dumps(extracted_data), quality_score)
    )
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return rid


def get_resume(resume_id, user_id):
    conn = get_connection()
    c = conn.cursor()
    row = c.execute(
        'SELECT * FROM resumes WHERE id = ? AND user_id = ?',
        (resume_id, user_id)
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d['extracted_data'] = json.loads(d['extracted_data'] or '{}')
        return d
    return None


def get_user_resumes(user_id):
    conn = get_connection()
    c = conn.cursor()
    rows = c.execute(
        'SELECT id, filename, file_type, quality_score, uploaded_at FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC',
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---- DEET registration operations ----

def save_registration(user_id, resume_id, registration_data, status='draft'):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        '''INSERT INTO deet_registrations (user_id, resume_id, registration_data, status)
           VALUES (?, ?, ?, ?)''',
        (user_id, resume_id, json.dumps(registration_data), status)
    )
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return rid


def submit_registration(reg_id, user_id, final_data):
    conn = get_connection()
    conn.execute(
        '''UPDATE deet_registrations
           SET registration_data = ?, status = 'submitted', submitted_at = ?
           WHERE id = ? AND user_id = ?''',
        (json.dumps(final_data), datetime.utcnow(), reg_id, user_id)
    )
    conn.commit()
    conn.close()


def get_user_registrations(user_id):
    conn = get_connection()
    c = conn.cursor()
    rows = c.execute(
        '''SELECT id, status, submitted_at, created_at FROM deet_registrations
           WHERE user_id = ? ORDER BY created_at DESC''',
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_registration(reg_id, user_id):
    conn = get_connection()
    c = conn.cursor()
    row = c.execute(
        'SELECT * FROM deet_registrations WHERE id = ? AND user_id = ?',
        (reg_id, user_id)
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d['registration_data'] = json.loads(d['registration_data'] or '{}')
        return d
    return None
