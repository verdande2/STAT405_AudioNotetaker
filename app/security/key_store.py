"""Persist and retrieve DB encryption keys for local app use."""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from pathlib import Path

APP_DIR_NAME = ".transcribenotes"
KEY_FILE_NAME = "db_key.bin"
KEY_FILE_ENV_VAR = "TRANSCRIBENOTES_KEY_FILE"
_DPAPI_PREFIX = b"DPAPI1\0"
_PLAINTEXT_PREFIX = b"PLAINTEXT1\0"


class KeyStoreError(RuntimeError):
    """Raised when the key store cannot save or load key material."""


def _candidate_key_file_paths() -> list[Path]:
    candidates: list[Path] = []

    env_path = os.getenv(KEY_FILE_ENV_VAR, "").strip()
    if env_path:
        candidates.append(Path(env_path).expanduser())

    local_app_data = os.getenv("LOCALAPPDATA", "").strip()
    if local_app_data:
        candidates.append(Path(local_app_data) / "TranscribeNotes" / KEY_FILE_NAME)

    candidates.append(Path.home() / APP_DIR_NAME / KEY_FILE_NAME)
    candidates.append(Path.cwd() / APP_DIR_NAME / KEY_FILE_NAME)
    return candidates


def save_database_key(key: str) -> Path:
    if not key or not key.strip():
        raise KeyStoreError("Database key cannot be empty.")

    encoded = key.strip().encode("utf-8")
    if os.name == "nt":
        payload = _DPAPI_PREFIX + _protect_windows(encoded)
    else:
        payload = _PLAINTEXT_PREFIX + encoded

    last_error: Exception | None = None
    for key_file in _candidate_key_file_paths():
        try:
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key_file.write_bytes(payload)
            try:
                os.chmod(key_file, 0o600)
            except OSError:
                # Windows permissions are ACL-based; chmod can fail harmlessly.
                pass
            return key_file
        except OSError as exc:
            last_error = exc

    raise KeyStoreError(f"Failed to save DB key: {last_error}")


def get_saved_database_key() -> str | None:
    for key_file in _candidate_key_file_paths():
        if not key_file.exists():
            continue

        payload = key_file.read_bytes()
        if payload.startswith(_DPAPI_PREFIX):
            if os.name != "nt":
                raise KeyStoreError("DPAPI key file cannot be read on this OS.")
            raw = _unprotect_windows(payload[len(_DPAPI_PREFIX) :])
            return raw.decode("utf-8")

        if payload.startswith(_PLAINTEXT_PREFIX):
            return payload[len(_PLAINTEXT_PREFIX) :].decode("utf-8")

        raise KeyStoreError("Unknown key file format.")

    return None


def clear_saved_database_key() -> None:
    for key_file in _candidate_key_file_paths():
        if key_file.exists():
            key_file.unlink()


if os.name == "nt":
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char)),
        ]


    def _buffer_to_blob(data: bytes) -> tuple[DATA_BLOB, ctypes.Array]:
        buf = ctypes.create_string_buffer(data)
        blob = DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
        return blob, buf


    def _blob_to_bytes(blob: DATA_BLOB) -> bytes:
        return ctypes.string_at(blob.pbData, blob.cbData)


    def _protect_windows(data: bytes) -> bytes:
        in_blob, in_buf = _buffer_to_blob(data)
        out_blob = DATA_BLOB()

        result = crypt32.CryptProtectData(
            ctypes.byref(in_blob),
            "TranscribeNotes DB Key",
            None,
            None,
            None,
            0,
            ctypes.byref(out_blob),
        )
        if not result:
            raise KeyStoreError(f"CryptProtectData failed: {ctypes.GetLastError()}")

        try:
            return _blob_to_bytes(out_blob)
        finally:
            if out_blob.pbData:
                kernel32.LocalFree(out_blob.pbData)


    def _unprotect_windows(data: bytes) -> bytes:
        in_blob, in_buf = _buffer_to_blob(data)
        out_blob = DATA_BLOB()

        result = crypt32.CryptUnprotectData(
            ctypes.byref(in_blob),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(out_blob),
        )
        if not result:
            raise KeyStoreError(f"CryptUnprotectData failed: {ctypes.GetLastError()}")

        try:
            return _blob_to_bytes(out_blob)
        finally:
            if out_blob.pbData:
                kernel32.LocalFree(out_blob.pbData)


else:

    def _protect_windows(data: bytes) -> bytes:
        raise KeyStoreError("Windows-only function called on non-Windows OS.")


    def _unprotect_windows(data: bytes) -> bytes:
        raise KeyStoreError("Windows-only function called on non-Windows OS.")
