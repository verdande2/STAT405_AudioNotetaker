def generate_theater_script(transcript: dict) -> str:
    """
    Produces a simple human-readable script with metadata header.
    """

    metadata = transcript.get("metadata", {})
    speakers = transcript.get("speakers", [])
    segments = transcript.get("segments", [])

    # Build speaker lookup
    speaker_lookup = {
        speaker["id"]: speaker.get("label", speaker["id"])
        for speaker in speakers
    }

    lines = []

    # ---- Metadata Header ----
    lines.append("=" * 40)
    lines.append("TRANSCRIPT")
    lines.append(f"Language: {metadata.get('language', 'unknown')}")
    lines.append(f"Model: {metadata.get('model', 'unknown')}")
    lines.append(f"Duration: {metadata.get('duration', 'unknown')} seconds")
    lines.append(f"Speakers: {metadata.get('num_speakers', len(speakers))}")
    lines.append(f"Generated: {metadata.get('created_at', 'unknown')}")
    lines.append("=" * 40)
    lines.append("")

    # ---- Dialogue ----
    for seg in segments:
        speaker_label = speaker_lookup.get(seg["speaker_id"], seg["speaker_id"])
        lines.append(f"{speaker_label}:")
        lines.append(seg["text"])
        lines.append("")  # spacing between lines

    return "\n".join(lines)
