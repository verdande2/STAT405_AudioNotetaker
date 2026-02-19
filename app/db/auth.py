"""Account/authentication helpers for admin-authorized local access."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

from app.db.database import connect_encrypted

PBKDF2_ITERATIONS = 600_000
BUILT_IN_ADMIN_USERNAME = "admin"
BUILT_IN_ADMIN_DISPLAY_NAME = "Class Admin"
BUILT_IN_ADMIN_PASSWORD_HASH = (
    "pbkdf2_sha256$600000$4f1c2da6f9a3bc117a5e0f8e2d93a4c1$"
    "1e13f24297ae576fb3a411bf0dc7ded94e7543810f3ab8f90324d5af39ed8bf7"
)


class AuthenticationError(RuntimeError):
    """Raised when credentials are invalid."""


class AuthorizationError(RuntimeError):
    """Raised when admin authorization requirements are not met."""


class AccountExistsError(RuntimeError):
    """Raised when attempting to create an account with an existing username."""


@dataclass(frozen=True)
class Account:
    id: int
    username: str
    display_name: str
    role: str
    is_active: bool


def _utc_now_expr() -> str:
    return "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"


def _password_hash(password: str, *, salt: bytes | None = None) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")

    salt_bytes = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        PBKDF2_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
        f"{salt_bytes.hex()}${digest.hex()}"
    )


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algo, iterations_str, salt_hex, hash_hex = stored_hash.split("$", maxsplit=3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, TypeError):
        return False

    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    ).hex()
    return hmac.compare_digest(computed, hash_hex)


def _row_to_account(row: tuple) -> Account:
    return Account(
        id=row[0],
        username=row[1],
        display_name=row[2],
        role=row[3],
        is_active=bool(row[4]),
    )


def _verify_built_in_admin_password(password: str) -> bool:
    return _verify_password(password, BUILT_IN_ADMIN_PASSWORD_HASH)


def _fetch_admin_account(conn) -> Account | None:
    row = conn.execute(
        """
        SELECT id, username, display_name, role, is_active
        FROM accounts
        WHERE role = 'admin'
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return None
    return _row_to_account(row)


def _ensure_built_in_admin_account(conn) -> Account:
    existing = _fetch_admin_account(conn)
    if existing is not None:
        return existing

    preferred = BUILT_IN_ADMIN_USERNAME
    username = preferred
    username_taken = conn.execute(
        "SELECT 1 FROM accounts WHERE username = ? COLLATE NOCASE LIMIT 1",
        (username,),
    ).fetchone()
    if username_taken:
        username = f"{preferred}_local"

    cursor = conn.execute(
        """
        INSERT INTO accounts (username, display_name, role, password_hash)
        VALUES (?, ?, 'admin', ?)
        """,
        (username, BUILT_IN_ADMIN_DISPLAY_NAME, BUILT_IN_ADMIN_PASSWORD_HASH),
    )
    account_id = cursor.lastrowid
    account = Account(
        id=account_id,
        username=username,
        display_name=BUILT_IN_ADMIN_DISPLAY_NAME,
        role="admin",
        is_active=True,
    )
    _log_event(
        conn,
        username_attempt=username,
        account_id=account.id,
        event_type="account_create",
        was_successful=True,
        details="Built-in class admin account created",
    )
    return account


def ensure_built_in_admin_account() -> Account:
    with connect_encrypted() as conn:
        account = _ensure_built_in_admin_account(conn)
        conn.commit()
        return account


def _log_event(
    conn,
    *,
    username_attempt: str,
    event_type: str,
    was_successful: bool,
    account_id: int | None = None,
    details: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO login_audit_events (
            username_attempt,
            account_id,
            event_type,
            was_successful,
            details
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            username_attempt,
            account_id,
            event_type,
            int(was_successful),
            details,
        ),
    )


def has_admin_account() -> bool:
    with connect_encrypted() as conn:
        return _fetch_admin_account(conn) is not None


def create_initial_admin_account(
    *,
    username: str,
    password: str,
    display_name: str,
) -> Account:
    if has_admin_account():
        raise AuthorizationError("An admin account already exists.")

    password_hash = _password_hash(password)

    with connect_encrypted() as conn:
        existing = conn.execute(
            "SELECT 1 FROM accounts WHERE username = ? COLLATE NOCASE",
            (username.strip(),),
        ).fetchone()
        if existing:
            raise AccountExistsError("Username is already in use.")

        cursor = conn.execute(
            """
            INSERT INTO accounts (username, display_name, role, password_hash)
            VALUES (?, ?, 'admin', ?)
            """,
            (username.strip(), display_name.strip(), password_hash),
        )
        account_id = cursor.lastrowid
        conn.commit()

    with connect_encrypted() as conn:
        _log_event(
            conn,
            username_attempt=username.strip(),
            account_id=account_id,
            event_type="account_create",
            was_successful=True,
            details="Initial admin account created",
        )
        conn.commit()
    return Account(account_id, username.strip(), display_name.strip(), "admin", True)


def authenticate_account(username: str, password: str) -> Account:
    with connect_encrypted() as conn:
        row = conn.execute(
            """
            SELECT id, username, display_name, role, is_active, password_hash
            FROM accounts
            WHERE username = ? COLLATE NOCASE
            LIMIT 1
            """,
            (username.strip(),),
        ).fetchone()

        if row is None:
            if _verify_built_in_admin_password(password):
                account = _ensure_built_in_admin_account(conn)
                conn.execute(
                    f"UPDATE accounts SET last_login_at = {_utc_now_expr()} WHERE id = ?",
                    (account.id,),
                )
                _log_event(
                    conn,
                    username_attempt=username.strip(),
                    account_id=account.id,
                    event_type="login",
                    was_successful=True,
                    details="Login via built-in class admin password",
                )
                conn.commit()
                return account

            _log_event(
                conn,
                username_attempt=username.strip(),
                event_type="login",
                was_successful=False,
                details="Unknown username",
            )
            conn.commit()
            raise AuthenticationError("Invalid username or password.")

        account = _row_to_account(row[:5])
        stored_hash = row[5]
        if not account.is_active or not _verify_password(password, stored_hash):
            _log_event(
                conn,
                username_attempt=username.strip(),
                account_id=account.id,
                event_type="login",
                was_successful=False,
                details="Invalid password or inactive account",
            )
            conn.commit()
            raise AuthenticationError("Invalid username or password.")

        conn.execute(
            f"UPDATE accounts SET last_login_at = {_utc_now_expr()} WHERE id = ?",
            (account.id,),
        )
        conn.commit()

        _log_event(
            conn,
            username_attempt=username.strip(),
            account_id=account.id,
            event_type="login",
            was_successful=True,
            details="Login successful",
        )
        conn.commit()
    return account


def create_psychologist_account(
    *,
    psychologist_username: str,
    psychologist_password: str,
    psychologist_display_name: str,
    admin_username: str | None = None,
    admin_password: str | None = None,
    admin_master_password: str | None = None,
    authorization_note: str = "In-person admin authorization",
) -> Account:
    if admin_master_password is not None:
        if not _verify_built_in_admin_password(admin_master_password):
            raise AuthenticationError("Invalid admin authorization password.")
        with connect_encrypted() as conn:
            admin = _ensure_built_in_admin_account(conn)
            conn.execute(
                f"UPDATE accounts SET last_login_at = {_utc_now_expr()} WHERE id = ?",
                (admin.id,),
            )
            _log_event(
                conn,
                username_attempt=admin.username,
                account_id=admin.id,
                event_type="login",
                was_successful=True,
                details="Admin authenticated via built-in authorization password",
            )
            conn.commit()
    else:
        if not admin_username or not admin_password:
            raise AuthorizationError(
                "Provide admin_username/admin_password or admin_master_password."
            )
        admin = authenticate_account(admin_username, admin_password)
        if admin.role != "admin":
            raise AuthorizationError("Only admin accounts can authorize psychologists.")

    password_hash = _password_hash(psychologist_password)
    username_clean = psychologist_username.strip()
    display_name_clean = psychologist_display_name.strip()

    with connect_encrypted() as conn:
        existing = conn.execute(
            "SELECT 1 FROM accounts WHERE username = ? COLLATE NOCASE LIMIT 1",
            (username_clean,),
        ).fetchone()
        if existing:
            raise AccountExistsError("Username is already in use.")

        cursor = conn.execute(
            """
            INSERT INTO accounts (username, display_name, role, password_hash)
            VALUES (?, ?, 'psychologist', ?)
            """,
            (username_clean, display_name_clean, password_hash),
        )
        psychologist_id = cursor.lastrowid

        conn.execute(
            """
            INSERT INTO admin_authorizations (
                psychologist_account_id,
                admin_account_id,
                note
            )
            VALUES (?, ?, ?)
            """,
            (psychologist_id, admin.id, authorization_note.strip()),
        )
        conn.commit()

    with connect_encrypted() as conn:
        _log_event(
            conn,
            username_attempt=username_clean,
            account_id=psychologist_id,
            event_type="admin_authorization",
            was_successful=True,
            details=f"Authorized by admin account id {admin.id}",
        )
        conn.commit()
    return Account(psychologist_id, username_clean, display_name_clean, "psychologist", True)


def is_psychologist_authorized(account_id: int) -> bool:
    with connect_encrypted() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM accounts a
            JOIN admin_authorizations aa
                ON aa.psychologist_account_id = a.id
            WHERE a.id = ?
              AND a.role = 'psychologist'
              AND a.is_active = 1
            LIMIT 1
            """,
            (account_id,),
        ).fetchone()
        return row is not None
