def convert_to_conversation_turns(transcript: dict) -> dict:
    """
    Converts segment-based transcript into conversation turn structure.
    Assumes segments are already merged appropriately.
    """

    segments = transcript.get("segments", [])
    turns = []

    for idx, seg in enumerate(segments):
        turns.append({
            "turn_id": idx,
            "speaker_id": seg["speaker_id"],
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"]
        })

    return {
        "metadata": transcript.get("metadata", {}),
        "speakers": transcript.get("speakers", []),
        "turns": turns
    }
