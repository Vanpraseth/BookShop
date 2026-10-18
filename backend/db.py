import os
import sqlite3
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATABASE_DIR = _PROJECT_ROOT / "database"
_DEFAULT_DB = _DATABASE_DIR / "bookshop.db"
_configured_db = os.environ.get("BOOKSHOP_DB", "").strip()
DB_PATH = Path(_configured_db or _DEFAULT_DB).expanduser()


def _enabled(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _open_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


def get_connection():
    return _open_connection()


def initialize_database():
    conn = _open_connection()
    try:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'users'"
        ).fetchone()
        if not exists:
            conn.executescript((_DATABASE_DIR / "schema.sql").read_text())
            if _enabled("SEED_CATALOGUE", default=True):
                conn.executescript((_DATABASE_DIR / "catalogue_data.sql").read_text())

        migrations_dir = _DATABASE_DIR / "migrations"
        if migrations_dir.exists():
            for migration in sorted(migrations_dir.glob("*.sql")):
                conn.executescript(migration.read_text())

        _create_initial_admin(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _create_initial_admin(conn):
    email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "")
    name = os.environ.get("ADMIN_NAME", "Store Administrator").strip()

    if not email and not password:
        return
    if not email or not password:
        raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD must be set together.")
    if len(password) < 12:
        raise RuntimeError("ADMIN_PASSWORD must contain at least 12 characters.")

    existing = conn.execute(
        "SELECT user_id FROM users WHERE lower(email) = lower(?)", (email,)
    ).fetchone()
    if existing:
        return

    from utils.security import hash_password

    cursor = conn.execute(
        "INSERT INTO users (full_name, email, password, role) VALUES (?, ?, ?, 'admin')",
        (name or "Store Administrator", email, hash_password(password)),
    )
    conn.execute("INSERT INTO carts (user_id) VALUES (?)", (cursor.lastrowid,))


def row_to_dict(row):
    return dict(row) if row is not None else None


def rows_to_list(rows):
    return [dict(r) for r in rows]
