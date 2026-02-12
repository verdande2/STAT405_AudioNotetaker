import json
from datetime import datetime
from pathlib import Path
from typing import Union


def convert_transcribe_anything_speakers_json(
    input_path: Union[str, Path],
    output_path: Union[str, Path] = None,
    model_name: str = "unknown",
    language: str = "unknown",
) -> dict:
    """
    Converts a transcribe-anything speaker.json file
    into a structured multi-speaker transcript schema.

    Parameters:
        input_path: Path to original speaker.json
        output_path: Optional path to save converted JSON
        model_name: Model name used for transcription
        language: Detected or assumed language

    Returns:
        structured transcript dictionary
    """

    input_path = Path(input_path)

    with open(input_path, "r", encoding="utf-8") as f:
        raw_segments = json.load(f)

    if not isinstance(raw_segments, list):
        raise ValueError("Input JSON must be a list of speaker segments.")

    # --- Collect unique speakers ---
    speaker_ids = sorted({seg["speaker"] for seg in raw_segments})

    speakers = []
    for idx, speaker_id in enumerate(speaker_ids):
        speakers.append({"id": speaker_id, "label": f"Speaker {idx + 1}"})

    # --- Convert segments ---
    structured_segments = []

    for idx, seg in enumerate(raw_segments):
        start, end = seg.get("timestamp", [None, None])

        structured_segment = {
            "segment_id": idx,
            "speaker_id": seg.get("speaker"),
            "start": float(start) if start is not None else None,
            "end": float(end) if end is not None else None,
            "text": seg.get("text", "").strip(),
        }

        # Preserve original diarization reason as switch_reason
        if "reason" in seg:
            structured_segment["switch_reason"] = seg["reason"]

        structured_segments.append(structured_segment)

    # --- Determine total duration ---
    duration = None
    if structured_segments:
        duration = max(s["end"] for s in structured_segments if s["end"] is not None)

    structured_output = {
        "metadata": {
            "language": language,
            "num_speakers": len(speakers),
            "model": model_name,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "duration": duration,
        },
        "speakers": speakers,
        "segments": structured_segments,
    }

    # --- Optional save ---
    if output_path:
        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(structured_output, f, indent=2, ensure_ascii=False)

    return structured_output
