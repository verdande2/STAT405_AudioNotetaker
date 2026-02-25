"""Audio upload processing pipeline with a placeholder transcription stage.

This service is intentionally structured as:
audio file -> transcription -> summarization -> DB persistence

Speech-to-text is not available yet, so `transcribe_audio` currently returns a
stub transcript while preserving the interface needed for future integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.db import create_session_record
from app.services.placeholder_transcript import (
    load_placeholder_transcript_json,
    load_placeholder_transcript_text,
)

try:
    from app.lm.Summarizer import Summary as LlamaSummary
except Exception:  # pragma: no cover - optional runtime dependency failures
    LlamaSummary = None


ProgressCallback = Callable[[int], None]


@dataclass(frozen=True)
class TranscriptStageOutput:
    transcript_json: dict
    transcript_text: str
    detected_language: str | None = None


@dataclass(frozen=True)
class ProcessedUploadResult:
    session_id: int
    source_audio_path: str
    transcript_text: str
    summary_text: str


class AudioSessionProcessor:
    """Process uploaded audio into stored session records."""

    def __init__(self, *, model_path: str | Path | None = None):
        self._model_path = Path(model_path) if model_path else self._resolve_default_model_path()
        self._summarizer = None

    def set_summarizer(self, summarizer) -> None:
        """Inject a preloaded summarizer instance from the UI layer."""
        self._summarizer = summarizer

    def set_model_path(self, model_path: str | Path | None) -> None:
        """Update the model path used if the processor needs to lazy-load."""
        self._model_path = Path(model_path) if model_path else None
        if self._summarizer is None:
            return
        # If the UI swaps models, force a fresh lazy load on next request unless
        # a new instance is explicitly injected via ``set_summarizer``.
        self._summarizer = None

    def process_audio_file(
        self,
        *,
        psychologist_account_id: int,
        client_profile_id: int,
        source_audio_path: str,
        progress_callback: ProgressCallback | None = None,
    ) -> ProcessedUploadResult:
        self._notify_progress(progress_callback, 10)

        transcript_output = self.transcribe_audio(source_audio_path)
        self._notify_progress(progress_callback, 55)

        summary_text = self.summarize_transcript(
            transcript_json=transcript_output.transcript_json,
            transcript_text=transcript_output.transcript_text,
        )
        self._notify_progress(progress_callback, 85)

        session = create_session_record(
            psychologist_account_id=psychologist_account_id,
            client_profile_id=client_profile_id,
            source_audio_path=source_audio_path,
            detected_language=transcript_output.detected_language,
            transcript_text=transcript_output.transcript_text,
            summary_text=summary_text,
        )
        self._notify_progress(progress_callback, 100)

        return ProcessedUploadResult(
            session_id=session.id,
            source_audio_path=source_audio_path,
            transcript_text=transcript_output.transcript_text,
            summary_text=summary_text,
        )

    def transcribe_audio(self, source_audio_path: str) -> TranscriptStageOutput:
        """Temporary speech-to-text placeholder.

        Replace this implementation with actual STT while preserving the return
        shape so the summarization and persistence stages do not need rewiring.
        """
        transcript_json = load_placeholder_transcript_json()
        transcript_text = load_placeholder_transcript_text()

        return TranscriptStageOutput(
            transcript_json=transcript_json,
            transcript_text=transcript_text,
            detected_language="en_US",
        )

    def summarize_transcript(self, *, transcript_json: dict, transcript_text: str) -> str:
        """Generate a summary using the local LLM summarizer when available."""
        # Temporary behavior: force a shared placeholder transcript into every
        # summarizer call until the real transcription stage is integrated.
        try:
            summarizer_input_json = load_placeholder_transcript_json()
            summarizer_input_text = load_placeholder_transcript_text()
        except Exception:
            summarizer_input_json = transcript_json
            summarizer_input_text = transcript_text

        summarizer = self._get_summarizer()
        if summarizer is None:
            return self._fallback_summary(summarizer_input_text)

        try:
            raw_output = summarizer.SummarizeSingle(transcript=summarizer_input_json)
        except Exception:
            return self._fallback_summary(summarizer_input_text)

        summary_text = self._extract_summary_text(raw_output)
        return summary_text or self._fallback_summary(summarizer_input_text)

    def _get_summarizer(self):
        if self._summarizer is not None:
            return self._summarizer
        if LlamaSummary is None or self._model_path is None or not self._model_path.exists():
            return None

        try:
            self._summarizer = LlamaSummary(path=str(self._model_path))
        except Exception:
            self._summarizer = None
        return self._summarizer

    def _resolve_default_model_path(self) -> Path | None:
        models_dir = Path("models")
        if not models_dir.exists():
            return None

        gguf_files = sorted(models_dir.glob("*.gguf"))
        if not gguf_files:
            return None
        return gguf_files[0]

    def _extract_summary_text(self, raw_output) -> str:
        if isinstance(raw_output, dict):
            choices = raw_output.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    text = first.get("text")
                    if isinstance(text, str):
                        return text.strip()
        return str(raw_output).strip() if raw_output is not None else ""

    def _fallback_summary(self, transcript_text: str) -> str:
        preview = " ".join(transcript_text.split())
        if len(preview) > 280:
            preview = preview[:277].rstrip() + "..."
        return (
            "Summary generated from placeholder transcript while speech-to-text is pending. "
            f"Transcript preview: {preview}"
        )

    @staticmethod
    def _notify_progress(progress_callback: ProgressCallback | None, value: int) -> None:
        if progress_callback is not None:
            progress_callback(max(0, min(100, int(value))))
