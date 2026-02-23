"""Quick SQLCipher health check for local encrypted DB setup."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db import DB_KEY_ENV_VAR, connect_encrypted, initialize_database, is_sqlite_header


def main() -> int:
    try:
        db_path = initialize_database()
    except Exception as exc:
        print(f"[ERROR] SQLCipher check failed: {exc}")
        print(
            f"[HINT] Set {DB_KEY_ENV_VAR}, or launch the app once to configure a saved key."
        )
        return 1

    print(f"[OK] Encrypted DB ready: {db_path}")
    print(f"[OK] Plain SQLite header present: {is_sqlite_header(db_path)}")
    print("[INFO] Expected header result for SQLCipher is: False")

    with connect_encrypted() as conn:
        schema_version = conn.execute("PRAGMA user_version").fetchone()[0]
        table_count = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type = 'table'"
        ).fetchone()[0]
    print(f"[OK] Schema version: {schema_version}")
    print(f"[OK] Table count: {table_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
