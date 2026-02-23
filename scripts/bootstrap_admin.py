"""Ensure the built-in class admin account exists on this laptop."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db import (
    AuthenticationError,
    BUILT_IN_ADMIN_USERNAME,
    authenticate_account,
    ensure_built_in_admin_account,
    initialize_database,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-password",
        action="store_true",
        help="Prompt for built-in admin password and verify it works",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    initialize_database()
    account = ensure_built_in_admin_account()

    print(
        f"[OK] Built-in admin account ready: id={account.id}, username={account.username}"
    )

    if not args.verify_password:
        return 0

    password = getpass.getpass("Built-in admin authorization password: ")
    try:
        admin = authenticate_account(BUILT_IN_ADMIN_USERNAME, password)
    except AuthenticationError as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[OK] Password verified for admin account id={admin.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
