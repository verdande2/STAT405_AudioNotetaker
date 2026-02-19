"""SQLCipher-backed local database bootstrap and connection utilities."""

from __future__ import annotations

import os
from pathlib import Path

from sqlcipher3 import dbapi2 as sqlite

from app.security import KeyStoreError, get_saved_database_key

DB_KEY_ENV_VAR = "TRANSCRIBENOTES_DB_KEY"
DB_PATH_ENV_VAR = "TRANSCRIBENOTES_DB_PATH"
DEFAULT_DB_PATH = Path("data") / "transcribenotes.db"
CURRENT_SCHEMA_VERSION = 2


class DatabaseInitializationError(RuntimeError):
    """Raised when encrypted DB configuration is missing or invalid."""


class MissingDatabaseKeyError(DatabaseInitializationError):
    """Raised when no DB key can be found from environment or local key store."""


class InvalidDatabaseKeyError(DatabaseInitializationError):
    """Raised when the provided key cannot decrypt the DB file."""


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL COLLATE NOCASE UNIQUE,
        display_name TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin', 'psychologist')),
        password_hash TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        last_login_at TEXT
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_single_admin_account
    ON accounts(role)
    WHERE role = 'admin'
    """,
    """
    CREATE TABLE IF NOT EXISTS admin_authorizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        psychologist_account_id INTEGER NOT NULL UNIQUE,
        admin_account_id INTEGER NOT NULL,
        note TEXT,
        authorized_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        FOREIGN KEY (psychologist_account_id) REFERENCES accounts(id) ON DELETE CASCADE,
        FOREIGN KEY (admin_account_id) REFERENCES accounts(id) ON DELETE RESTRICT,
        CHECK (psychologist_account_id <> admin_account_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS login_audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username_attempt TEXT NOT NULL,
        account_id INTEGER,
        event_type TEXT NOT NULL CHECK (
            event_type IN ('login', 'admin_authorization', 'account_create')
        ),
        was_successful INTEGER NOT NULL CHECK (was_successful IN (0, 1)),
        details TEXT,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS client_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        psychologist_account_id INTEGER NOT NULL,
        client_code TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        dob TEXT,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        FOREIGN KEY (psychologist_account_id) REFERENCES accounts(id) ON DELETE CASCADE,
        UNIQUE (psychologist_account_id, client_code)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_client_profiles_psychologist
    ON client_profiles(psychologist_account_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS session_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        psychologist_account_id INTEGER NOT NULL,
        client_profile_id INTEGER NOT NULL,
        source_audio_path TEXT NOT NULL,
        detected_language TEXT,
        transcript_text TEXT,
        summary_text TEXT,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        FOREIGN KEY (psychologist_account_id) REFERENCES accounts(id) ON DELETE CASCADE,
        FOREIGN KEY (client_profile_id) REFERENCES client_profiles(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_session_records_psychologist
    ON session_records(psychologist_account_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_session_records_client
    ON session_records(client_profile_id)
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_client_profiles_updated_at
    AFTER UPDATE ON client_profiles
    FOR EACH ROW
    BEGIN
        UPDATE client_profiles
        SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
        WHERE id = OLD.id;
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_session_records_owner_insert
    BEFORE INSERT ON session_records
    FOR EACH ROW
    BEGIN
        SELECT CASE
            WHEN (
                SELECT psychologist_account_id
                FROM client_profiles
                WHERE id = NEW.client_profile_id
            ) IS NULL
                THEN RAISE(ABORT, 'client_profile_not_found')
            WHEN (
                SELECT psychologist_account_id
                FROM client_profiles
                WHERE id = NEW.client_profile_id
            ) != NEW.psychologist_account_id
                THEN RAISE(ABORT, 'cross_account_session_forbidden')
        END;
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_session_records_owner_update
    BEFORE UPDATE OF psychologist_account_id, client_profile_id ON session_records
    FOR EACH ROW
    BEGIN
        SELECT CASE
            WHEN (
                SELECT psychologist_account_id
                FROM client_profiles
                WHERE id = NEW.client_profile_id
            ) IS NULL
                THEN RAISE(ABORT, 'client_profile_not_found')
            WHEN (
                SELECT psychologist_account_id
                FROM client_profiles
                WHERE id = NEW.client_profile_id
            ) != NEW.psychologist_account_id
                THEN RAISE(ABORT, 'cross_account_session_forbidden')
        END;
    END
    """,
)


MIGRATION_STATEMENTS = (
    # v1 -> v2: introduce psychologist account ownership on legacy tables.
    "ALTER TABLE patients ADD COLUMN psychologist_account_id INTEGER",
    "ALTER TABLE sessions ADD COLUMN psychologist_account_id INTEGER",
)


def resolve_db_path() -> Path:
    """Resolve DB location from env or fallback path."""
    raw_path = os.getenv(DB_PATH_ENV_VAR)
    db_path = Path(raw_path).expanduser() if raw_path else DEFAULT_DB_PATH
    return db_path.resolve()


def get_database_key() -> str:
    """Read the first available SQLCipher key candidate."""
    candidates = _get_database_key_candidates()
    if not candidates:
        raise MissingDatabaseKeyError(
            f"Missing {DB_KEY_ENV_VAR} and no saved key found."
        )
    return candidates[0]


def _get_database_key_candidates() -> list[str]:
    """Return unique key candidates from env and local key store."""
    candidates: list[str] = []

    env_key = os.getenv(DB_KEY_ENV_VAR, "").strip()
    if env_key:
        candidates.append(env_key)

    try:
        saved_key = get_saved_database_key()
    except KeyStoreError as exc:
        raise DatabaseInitializationError(f"Failed to read saved DB key: {exc}") from exc

    if saved_key and saved_key not in candidates:
        candidates.append(saved_key)

    return candidates


def _apply_cipher_pragmas(conn: sqlite.Connection, key: str) -> None:
    escaped_key = key.replace("'", "''")
    conn.execute(f"PRAGMA key = '{escaped_key}'")
    conn.execute("PRAGMA cipher_compatibility = 4")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA secure_delete = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    # Triggers key validation immediately and fails fast on wrong keys.
    conn.execute("SELECT count(*) FROM sqlite_master")


def connect_encrypted() -> sqlite.Connection:
    """Create a SQLCipher connection with security pragmas applied."""
    db_path = resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    key_candidates = _get_database_key_candidates()
    if not key_candidates:
        raise MissingDatabaseKeyError(
            f"Missing {DB_KEY_ENV_VAR} and no saved key found."
        )

    last_exc: Exception | None = None
    for key in key_candidates:
        conn = sqlite.connect(str(db_path))
        try:
            _apply_cipher_pragmas(conn, key)
            return conn
        except sqlite.DatabaseError as exc:
            conn.close()
            last_exc = exc

    raise InvalidDatabaseKeyError(
        "Unable to decrypt database with available key material."
    ) from last_exc


def _table_exists(conn: sqlite.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(conn: sqlite.Connection, table_name: str, column_name: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


def _apply_legacy_migrations(conn: sqlite.Connection, schema_version: int) -> None:
    if schema_version >= 2:
        return

    for statement in MIGRATION_STATEMENTS:
        table_name = "patients" if "patients" in statement else "sessions"
        column_name = "psychologist_account_id"
        if _table_exists(conn, table_name) and not _column_exists(conn, table_name, column_name):
            conn.execute(statement)


def initialize_database() -> Path:
    """Create the encrypted DB file and ensure baseline schema exists."""
    db_path = resolve_db_path()
    with connect_encrypted() as conn:
        schema_version = conn.execute("PRAGMA user_version").fetchone()[0]
        _apply_legacy_migrations(conn, schema_version)

        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)

        conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
        conn.commit()
    return db_path


def is_sqlite_header(db_path: Path) -> bool:
    """Check for plaintext SQLite header (should be False for SQLCipher DB files)."""
    if not db_path.exists():
        return False
    with db_path.open("rb") as file:
        return file.read(16) == b"SQLite format 3\x00"
