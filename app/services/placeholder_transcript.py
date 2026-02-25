"""Shared placeholder transcript data used until STT is integrated."""

from __future__ import annotations

import re
from pathlib import Path

_SPEAKER_TURN_PATTERN = re.compile(
    r"(Psychologist|Client):\s*(.*?)(?=(?:Psychologist|Client):|$)",
    flags=re.IGNORECASE | re.DOTALL,
)


def placeholder_transcript_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sample_data" / "placeholder_psychology_session.txt"


def load_placeholder_transcript_text() -> str:
    text = placeholder_transcript_path().read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Placeholder transcript file is empty.")
    return text


def load_placeholder_transcript_json() -> dict[str, dict[str, str]]:
    text = load_placeholder_transcript_text()
    transcript: dict[str, dict[str, str]] = {}

    for idx, match in enumerate(_SPEAKER_TURN_PATTERN.finditer(text)):
        speaker = match.group(1).strip().capitalize()
        utterance = " ".join(match.group(2).split())
        if not utterance:
            continue
        transcript[str(idx)] = {"speaker": speaker, "text": utterance}

    if not transcript:
        raise ValueError(
            "Placeholder transcript file must contain speaker-labeled turns like "
            "'Psychologist: ... Client: ...'."
        )

    return transcript

