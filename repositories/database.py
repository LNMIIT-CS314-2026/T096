import sqlite3
from config import Config

def get_db_connection() -> sqlite3.Connection:
    """Creates a connection to SQLite database with dictionary-like row access and WAL mode."""
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db() -> None:
    """Initializes tables for IQAC Activity Tracking System at a clean, surface level."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS departments (
        department_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        head_of_dept TEXT,
        contact_info TEXT
    );

    CREATE TABLE IF NOT EXISTS domain_areas (
        domain_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        department_id TEXT,
        contact_info TEXT,
        account_status TEXT DEFAULT 'ACTIVE',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
    );

    CREATE TABLE IF NOT EXISTS activities (
        activity_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        domain_id TEXT,
        department_id TEXT NOT NULL,
        created_by TEXT NOT NULL,
        assigned_to TEXT,
        planned_start TEXT,
        deadline TEXT NOT NULL,
        priority TEXT NOT NULL,
        status TEXT NOT NULL,
        outcome TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (domain_id) REFERENCES domain_areas(domain_id),
        FOREIGN KEY (department_id) REFERENCES departments(department_id),
        FOREIGN KEY (created_by) REFERENCES users(user_id),
        FOREIGN KEY (assigned_to) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS evidence (
        evidence_id TEXT PRIMARY KEY,
        activity_id TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        description TEXT,
        verification_status TEXT NOT NULL,
        uploaded_by TEXT NOT NULL,
        uploaded_at TEXT NOT NULL,
        FOREIGN KEY (activity_id) REFERENCES activities(activity_id) ON DELETE CASCADE,
        FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS verifications (
        verification_id TEXT PRIMARY KEY,
        activity_id TEXT NOT NULL,
        verified_by TEXT NOT NULL,
        decision TEXT NOT NULL,
        comments TEXT,
        decision_date TEXT NOT NULL,
        FOREIGN KEY (activity_id) REFERENCES activities(activity_id) ON DELETE CASCADE,
        FOREIGN KEY (verified_by) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS notifications (
        notification_id TEXT PRIMARY KEY,
        recipient TEXT NOT NULL,
        message TEXT NOT NULL,
        notification_type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (recipient) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS activity_history_log (
        log_id TEXT PRIMARY KEY,
        activity_id TEXT NOT NULL,
        performed_by TEXT NOT NULL,
        action TEXT NOT NULL,
        old_value TEXT,
        new_value TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (activity_id) REFERENCES activities(activity_id) ON DELETE CASCADE,
        FOREIGN KEY (performed_by) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS otp_verifications (
        otp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        otp_code TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        is_used INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS feedback_forms (
        form_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        activity_id TEXT NOT NULL,
        target_role TEXT DEFAULT 'STUDENT',
        is_open INTEGER DEFAULT 1,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (activity_id) REFERENCES activities(activity_id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS feedback_responses (
        response_id TEXT PRIMARY KEY,
        form_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        rating INTEGER NOT NULL,
        comments TEXT,
        submitted_at TEXT NOT NULL,
        UNIQUE(form_id, user_id),
        FOREIGN KEY (form_id) REFERENCES feedback_forms(form_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS admin_audit_log (
        audit_id TEXT PRIMARY KEY,
        admin_id TEXT NOT NULL,
        target_user_id TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (admin_id) REFERENCES users(user_id)
    );
    """)

    conn.commit()

    # Migration check for planned_start if table existed
    try:
        cursor.execute("ALTER TABLE activities ADD COLUMN planned_start TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    conn.close()
