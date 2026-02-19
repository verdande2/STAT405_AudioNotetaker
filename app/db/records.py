"""Psychologist-scoped client/session storage helpers."""

from __future__ import annotations

from dataclasses import dataclass

from app.db.auth import AuthorizationError, is_psychologist_authorized
from app.db.database import connect_encrypted
from sqlcipher3 import dbapi2 as sqlite


@dataclass(frozen=True)
class ClientProfile:
    id: int
    psychologist_account_id: int
    client_code: str
    first_name: str | None
    last_name: str | None
    dob: str | None
    notes: str | None


@dataclass(frozen=True)
class SessionRecord:
    id: int
    psychologist_account_id: int
    client_profile_id: int
    source_audio_path: str
    detected_language: str | None
    transcript_text: str | None
    summary_text: str | None
    created_at: str


@dataclass(frozen=True)
class RecordCounts:
    client_count: int
    session_count: int


def _row_to_client(row: tuple) -> ClientProfile:
    return ClientProfile(
        id=row[0],
        psychologist_account_id=row[1],
        client_code=row[2],
        first_name=row[3],
        last_name=row[4],
        dob=row[5],
        notes=row[6],
    )


def _row_to_session(row: tuple) -> SessionRecord:
    return SessionRecord(
        id=row[0],
        psychologist_account_id=row[1],
        client_profile_id=row[2],
        source_audio_path=row[3],
        detected_language=row[4],
        transcript_text=row[5],
        summary_text=row[6],
        created_at=row[7],
    )


def _assert_authorized_psychologist(psychologist_account_id: int) -> None:
    if not is_psychologist_authorized(psychologist_account_id):
        raise AuthorizationError(
            "Psychologist account is not active and admin-authorized on this device."
        )


def create_client_profile(
    *,
    psychologist_account_id: int,
    client_code: str,
    first_name: str | None = None,
    last_name: str | None = None,
    dob: str | None = None,
    notes: str | None = None,
) -> ClientProfile:
    _assert_authorized_psychologist(psychologist_account_id)
    with connect_encrypted() as conn:
        cursor = conn.execute(
            """
            INSERT INTO client_profiles (
                psychologist_account_id,
                client_code,
                first_name,
                last_name,
                dob,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                psychologist_account_id,
                client_code.strip(),
                first_name.strip() if first_name else None,
                last_name.strip() if last_name else None,
                dob.strip() if dob else None,
                notes.strip() if notes else None,
            ),
        )
        client_id = cursor.lastrowid
        conn.commit()

        row = conn.execute(
            """
            SELECT
                id,
                psychologist_account_id,
                client_code,
                first_name,
                last_name,
                dob,
                notes
            FROM client_profiles
            WHERE id = ?
            """,
            (client_id,),
        ).fetchone()
        return _row_to_client(row)


def list_client_profiles(psychologist_account_id: int) -> list[ClientProfile]:
    _assert_authorized_psychologist(psychologist_account_id)
    with connect_encrypted() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                psychologist_account_id,
                client_code,
                first_name,
                last_name,
                dob,
                notes
            FROM client_profiles
            WHERE psychologist_account_id = ?
            ORDER BY created_at DESC
            """,
            (psychologist_account_id,),
        ).fetchall()
    return [_row_to_client(row) for row in rows]


def create_session_record(
    *,
    psychologist_account_id: int,
    client_profile_id: int,
    source_audio_path: str,
    detected_language: str | None = None,
    transcript_text: str | None = None,
    summary_text: str | None = None,
) -> SessionRecord:
    _assert_authorized_psychologist(psychologist_account_id)
    try:
        with connect_encrypted() as conn:
            cursor = conn.execute(
                """
                INSERT INTO session_records (
                    psychologist_account_id,
                    client_profile_id,
                    source_audio_path,
                    detected_language,
                    transcript_text,
                    summary_text
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    psychologist_account_id,
                    client_profile_id,
                    source_audio_path.strip(),
                    detected_language.strip() if detected_language else None,
                    transcript_text,
                    summary_text,
                ),
            )
            session_id = cursor.lastrowid
            conn.commit()

            row = conn.execute(
                """
                SELECT
                    id,
                    psychologist_account_id,
                    client_profile_id,
                    source_audio_path,
                    detected_language,
                    transcript_text,
                    summary_text,
                    created_at
                FROM session_records
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
            return _row_to_session(row)
    except sqlite.IntegrityError as exc:
        if "cross_account_session_forbidden" in str(exc):
            raise AuthorizationError(
                "Cannot store a session for a client owned by another psychologist."
            ) from exc
        raise


def list_session_records(
    psychologist_account_id: int,
    *,
    client_profile_id: int | None = None,
) -> list[SessionRecord]:
    _assert_authorized_psychologist(psychologist_account_id)
    with connect_encrypted() as conn:
        if client_profile_id is None:
            rows = conn.execute(
                """
                SELECT
                    id,
                    psychologist_account_id,
                    client_profile_id,
                    source_audio_path,
                    detected_language,
                    transcript_text,
                    summary_text,
                    created_at
                FROM session_records
                WHERE psychologist_account_id = ?
                ORDER BY created_at DESC
                """,
                (psychologist_account_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    id,
                    psychologist_account_id,
                    client_profile_id,
                    source_audio_path,
                    detected_language,
                    transcript_text,
                    summary_text,
                    created_at
                FROM session_records
                WHERE psychologist_account_id = ?
                  AND client_profile_id = ?
                ORDER BY created_at DESC
                """,
                (psychologist_account_id, client_profile_id),
            ).fetchall()
    return [_row_to_session(row) for row in rows]


def get_record_counts(psychologist_account_id: int) -> RecordCounts:
    _assert_authorized_psychologist(psychologist_account_id)
    with connect_encrypted() as conn:
        client_count = conn.execute(
            """
            SELECT count(*)
            FROM client_profiles
            WHERE psychologist_account_id = ?
            """,
            (psychologist_account_id,),
        ).fetchone()[0]
        session_count = conn.execute(
            """
            SELECT count(*)
            FROM session_records
            WHERE psychologist_account_id = ?
            """,
            (psychologist_account_id,),
        ).fetchone()[0]
    return RecordCounts(client_count=client_count, session_count=session_count)


def delete_session_record(
    *,
    psychologist_account_id: int,
    session_record_id: int,
) -> bool:
    _assert_authorized_psychologist(psychologist_account_id)
    with connect_encrypted() as conn:
        cursor = conn.execute(
            """
            DELETE FROM session_records
            WHERE id = ?
              AND psychologist_account_id = ?
            """,
            (session_record_id, psychologist_account_id),
        )
        conn.commit()
    return cursor.rowcount > 0


def delete_client_profile(
    *,
    psychologist_account_id: int,
    client_profile_id: int,
) -> bool:
    _assert_authorized_psychologist(psychologist_account_id)
    with connect_encrypted() as conn:
        cursor = conn.execute(
            """
            DELETE FROM client_profiles
            WHERE id = ?
              AND psychologist_account_id = ?
            """,
            (client_profile_id, psychologist_account_id),
        )
        conn.commit()
    return cursor.rowcount > 0
