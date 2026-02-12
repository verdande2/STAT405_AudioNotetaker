def convert_to_chat_style(transcript: dict) -> list:
    """
    Converts transcript into chat-style format:
    [
        {"role": "Speaker 1", "content": "..."},
        ...
    ]
    """

    speaker_lookup = {
        speaker["id"]: speaker.get("label", speaker["id"])
        for speaker in transcript.get("speakers", [])
    }

    chat_output = []

    for seg in transcript.get("segments", []):
        chat_output.append({
            "role": speaker_lookup.get(seg["speaker_id"], seg["speaker_id"]),
            "content": seg["text"]
        })

    return chat_output
