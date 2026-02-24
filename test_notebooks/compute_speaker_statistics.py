def compute_speaker_statistics(transcript: dict) -> dict:
    """
    Computes total speaking time and percentage for each speaker.
    Returns structured statistics.
    """

    segments = transcript.get("segments", [])
    speakers = transcript.get("speakers", [])

    speaking_time = {}

    total_time = 0.0

    for seg in segments:
        start = seg.get("start")
        end = seg.get("end")

        if start is None or end is None:
            continue

        duration = max(0.0, end - start)
        total_time += duration

        speaker_id = seg["speaker_id"]
        speaking_time[speaker_id] = speaking_time.get(speaker_id, 0.0) + duration

    # Add percentage breakdown
    stats = []
    for speaker in speakers:
        sid = speaker["id"]
        duration = speaking_time.get(sid, 0.0)

        stats.append({
            "speaker_id": sid,
            "label": speaker.get("label"),
            "speaking_time_seconds": round(duration, 3),
            "percentage_of_total": round(
                (duration / total_time * 100) if total_time > 0 else 0.0, 2
            )
        })

    return {
        "total_duration_seconds": round(total_time, 3),
        "speaker_statistics": stats
    }
