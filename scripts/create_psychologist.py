"""Create a psychologist account with in-person admin authorization."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db import (
    AccountExistsError,
    AuthenticationError,
    AuthorizationError,
    BUILT_IN_ADMIN_USERNAME,
    create_psychologist_account,
    initialize_database,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--psych-username",
        help="Psychologist login username (spaces allowed)",
    )
    parser.add_argument(
        "--psych-display-name",
        help="Psychologist display name",
    )
    parser.add_argument(
        "--admin-username",
        default=BUILT_IN_ADMIN_USERNAME,
        help="Admin username authorizing this psychologist (account mode only)",
    )
    parser.add_argument(
        "--use-master-admin-password",
        action="store_true",
        help="Authorize with built-in class admin password instead of admin account password",
    )
    parser.add_argument(
        "--note",
        default="In-person admin authorization",
        help="Authorization note",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    initialize_database()

    psych_username = (args.psych_username or "").strip()
    if not psych_username:
        psych_username = input("Psychologist username (spaces allowed): ").strip()
    if not psych_username:
        print("[ERROR] Psychologist username is required.")
        return 1

    psych_display_name = (args.psych_display_name or "").strip()
    if not psych_display_name:
        psych_display_name = input("Psychologist display name: ").strip()
    if not psych_display_name:
        psych_display_name = psych_username

    psych_password = getpass.getpass("Psychologist password: ")
    psych_confirm = getpass.getpass("Confirm psychologist password: ")
    if psych_password != psych_confirm:
        print("[ERROR] Psychologist passwords did not match.")
        return 1

    admin_password: str | None = None
    admin_master_password: str | None = None
    if args.use_master_admin_password:
        admin_master_password = getpass.getpass(
            "Built-in admin authorization password: "
        )
    else:
        admin_password = getpass.getpass("Admin password (for authorization): ")

    try:
        account = create_psychologist_account(
            psychologist_username=psych_username,
            psychologist_password=psych_password,
            psychologist_display_name=psych_display_name,
            admin_username=args.admin_username,
            admin_password=admin_password,
            admin_master_password=admin_master_password,
            authorization_note=args.note,
        )
    except (AuthenticationError, AuthorizationError, AccountExistsError) as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(
        f"[OK] Psychologist account created: id={account.id}, username={account.username}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
