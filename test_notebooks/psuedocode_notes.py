# transcript post-processing psuedocode:

# transcript = normalize_speaker_ids(transcript) # likely unneeded if speakers are already normalized
# transcript = merge_consecutive_same_speaker_segments(transcript) # Merges back-to-back segments if: Same speaker_id AND gap <= tolerance
# conversation = convert_to_conversation_turns(transcript) # Transforms segment-based transcript into turn-based structure.
# stats = compute_speaker_statistics(transcript) # returns dict of audio stats, total duration, and speaker stats: label/name, speaking time, percentage of total, etc
# chat_format = convert_to_chat_style(transcript) # distill the transcription into a speaker1: words, speaker2: words, speaker1: words etc json format
# script_text = generate_theater_script(transcript) raw text transcript, summary at top, then speaker:\n words style dialogue

# consumer gets a transcription result output, depending on their desired format:

# example convert_to_chat_style() output:
# [
#     {"role": "Speaker 1", "content": "Hello"},
#     {"role": "Speaker 2", "content": "Hi there"}
# ]

# example convert_to_conversation_turns() output:
# {
#     "metadata": {
#         "language": "en-US",
#         "num_speakers": 2,
#         "model": "whisper-large-v3",
#         # "model_version": "3.0",
#         # "model_size": "large",
#         "created_at": "2026-02-12T12:00:00Z",
#         "duration": 342.21,
#     },
#     "turns": [
#         {"turn_id": 0, "speaker_id": "SPEAKER_00", "start": 0.0, "end": 6.3, "text": "Hello there..."},
#         {"turn_id": 1, "speaker_id": "SPEAKER_01", "start": 8.3, "end": 12.3, "text": "Howdy ho!"}
#     ]
# }

# example generate_theater_script() output:
# ====================================
# TRANSCRIPT
# Language: en
# Model: whisper-large-v3
# Duration: 342.21 seconds
# Speakers: 2
# Generated: 2026-02-12T12:00:00Z
# ====================================

# Speaker 1:
# Hello, how are you?

# Speaker 2:
# I'm fine, thank you.

# Speaker 1:
# Excellent, what did you do today?
