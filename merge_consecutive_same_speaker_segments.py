def merge_consecutive_same_speaker_segments(transcript: dict, gap_tolerance: float = 0.5) -> dict:
    """
    Merges consecutive segments if they belong to the same speaker
    and the time gap between them is <= gap_tolerance seconds.
    """

    segments = transcript.get("segments", [])
    if not segments:
        return transcript

    merged = []
    current = segments[0].copy()

    for next_seg in segments[1:]:
        same_speaker = next_seg["speaker_id"] == current["speaker_id"]
        gap = next_seg["start"] - current["end"]

        if same_speaker and gap <= gap_tolerance:
            # Merge
            current["end"] = next_seg["end"]
            current["text"] += " " + next_seg["text"]

            # Preserve switch_reason if meaningful
            if "switch_reason" in next_seg:
                current.setdefault("merged_reasons", []).append(next_seg["switch_reason"])
        else:
            merged.append(current)
            current = next_seg.copy()

    merged.append(current)

    # Reassign segment IDs
    for idx, seg in enumerate(merged):
        seg["segment_id"] = idx

    transcript["segments"] = merged
    return transcript
