import os
import pytest
# from datasets import load_dataset, Audio

from app.src.AudioTranscriber.AudioTranscriber import AudioTranscriber
from app.src.TranscriptTranslator.TranscriptTranslator import TranscriptTranslator

# aight, let's give this pytest thing a shot, eh?

# note: pytest will automatically inject `samples()` as `samples` anywhere it is used in session
@pytest.fixture(scope="session")
def samples():
    # ds = load_dataset(
    #     "fsicolo/common_voice_22_0", "en",
    #     split="test",
    #     trust_remote_code=True,
    #     cache_dir=os.environ.get("HF_DATASETS_CACHE"),
    # )
    # ds = ds.cast_column("audio", Audio(sampling_rate=16_000))
    # return [ds[i] for i in range(32)]
    return ["blah" for i in range(32)]


@pytest.fixture(scope="module")
def transcriber():
    audio_transcriber = AudioTranscriber()
    audio_transcriber.enable_online_mode() # TODO consider tests in offline mode? or do proper mocks? later ...
    audio_transcriber.set_hf_token(os.environ.get("HF_TOKEN"))
    return audio_transcriber
    
    
@pytest.fixture(scope="module")
def translator():
    return TranscriptTranslator() # no transcript JSON set for init