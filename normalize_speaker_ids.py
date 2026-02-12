def normalize_speaker_ids(transcript: dict) -> dict:
    """
    Normalizes speaker IDs to sequential SPEAKER_00, SPEAKER_01, ...
    Updates both speakers list and segment references.
    """

    segments = transcript.get("segments", [])
    speakers = transcript.get("speakers", [])

    # Collect unique speaker IDs in order of first appearance
    seen = []
    for seg in segments:
        if seg["speaker_id"] not in seen:
            seen.append(seg["speaker_id"])

    mapping = {
        old_id: f"SPEAKER_{str(i).zfill(2)}"
        for i, old_id in enumerate(seen)
    }

    # Update segments
    for seg in segments:
        seg["speaker_id"] = mapping[seg["speaker_id"]]

    # Update speakers section
    normalized_speakers = []
    for i, old_id in enumerate(seen):
        normalized_speakers.append({
            "id": mapping[old_id],
            "label": f"Speaker {i + 1}"
        })

    transcript["segments"] = segments
    transcript["speakers"] = normalized_speakers
    transcript["metadata"]["num_speakers"] = len(normalized_speakers)

    return transcript
