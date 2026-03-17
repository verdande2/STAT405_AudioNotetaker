from __future__ import annotations
from typing import List, Dict, Optional, Union
from pathlib import Path
import json, logging, time, subprocess, re, sys, time, os, platform, psutil
from datetime import datetime, timedelta
import whisperx
from faster_whisper import WhisperModel
import numpy as np
from dataclasses import dataclass, field
from app.src.WhisperXConfig.WhisperXConfig import WhisperXConfig, auto_configure_whisperx
from app.src.ffmpeg_utils import ffmpeg_utils
from app.src.utils.utils import print_formatted_sys_path, ensure_ffmpeg_installed, format_timestamp
from iso639 import Lang, iter_langs


DEBUG_MODE = True

# basic logging setup, default handler outputs to stdout already, # TODO maybe add a file output handler to log to a local log file (temp file, etc), or log records to the db? What schema for log record table? Timestamp, exception class name, exception message text, maybe a join'd traceback string too? ehhhhh, not important right now. Will resort to additional logging behaviors as needed, /if/ needed...

# TODO cleanup debug/logging calls/output in this class def file...
logging.basicConfig(level=logging.INFO if not DEBUG_MODE else logging.DEBUG)  # toggle debug output here
logging.info(f"Basic logger setup!")

class AudioTranscriber():
    """
    A class interface for transcribing audio files into structured json output (or a variety of other formats).

    This class encapsulates the workflow for:
        - Managing an input audio file path (assumed mp4 audio format (AAC codec))
        - Detecting the spoken language
        - Performing transcription/translation/diarization/word-level timestamp alignment, etc
        - Outputting the raw JSON transcript, or a formatted human-readable "script"-style text transcript, etc
        - Assigning metadata to the transcript JSON
    """
    
    _filepath = None # Path object
    _transcript = None # JSON transcript result and metadata
    _hf_token = None # HuggingFace token for downloading gated models
    _online_mode = True # default to online mode, set to False to disable online mode after first run, will utilize cached models only
    _execution_times = {} # dict of execution times for various stages of the transcription process
    _whisperx_cfg = None # WhisperX config object
    
    def __init__(self, filepath: Optional[Union[str, Path]] = None):
        """
        Initialize the AudioTranscriber.

        Args:
            filepath:
                (Optional) path (str or pathlib.Path) to the audio file (mp4 with AAC codec assumed, but literally anything that ffmpeg will accept should be fine) to transcribe.
        """
        
        # prepare yourself, this is gonna be a doozy of a dunder init method...
        
        # first off, let's get everything checked and set up during initialization
        if DEBUG_MODE:
            print(
                f"\033[31m WARNING: DEBUG MODE is ON! \033[0m Verbose output and debug logging enabled."
            )
            
        init_start_time = time.perf_counter()  # begin timer for determining init/setup time # TODO perhaps a better, neater way to time code execution? timeit or similar? or just be lazy and continue using time.perf_counter() because its so straightforward and doesn't add any significant overhead/dependencies?
        logging.info(f"AudioTranscriber __init__()! Start time: {datetime.now()}")
            
        # checking offline mode toggle flags
        if os.environ.get("HF_HUB_OFFLINE") == "1": # directly pulls from environment
            logging.info(
                # blue text indicating offline mode active
                f"\033[94m HF Hub Offline mode set. \033[0m Will use local (cached) models only." # # TODO FIXME "allegedly" local only, but somehow urllib3 is processing HTTPS requests according to the debug log... but offline mode is enabled... maybe there is a dependency that is still phoning home for model information and needs some quick and effective STFU treatment?investigate me! the hell? Stahp, urllib...... STAHP!
            )
        else:
            logging.warning(
                # red warning text indicating to user that online mode is ACTIVE, and will require network connection for initial downloading of models to a local cache
                f"\033[31m Warning! HF Hub Online mode set! \033[0m This will be _slow_ (internet download speed dependent) for initial run, but once models have been downloaded and cached locally, set `os.environ['HF_HUB_OFFLINE'] = \"1\"` to disable online mode and use only the local (cached) models (network connection/internet access should _not_ be required after that point)."
            )

        if os.environ.get("TRANSFORMERS_OFFLINE") == "1": # directly pulls from environment
            logging.info(
                # blue text indicating offline mode active
                f"\033[94m Transformers Offline mode set. \033[0m"
            )
        else:
            logging.warning(
                # red warning text indicating to user that transformers online mode is ACTIVE, and will require network connection for initial downloading of models to a local cache through transformers load functions
                f"\033[31m Warning! Transformers Online mode set! \033[0m This could take a bit depending on hardware specs and network connection."
            )

        # TODO consider doublechecking HF_DATASETS_OFFLINE = 1? should just be needed for the test datasets, not here...

        # test torch/torchaudio/pyannote.audio versions, refer to compatability table on GitHub for more info
        import torch
        import torchaudio
        import pyannote.audio
        
        if DEBUG_MODE:
            logging.info(f"Checking versions of torch, torchaudio, and pyannote.audio...")
            logging.info(f"{torch.__version__=}")
            logging.info(f"{torchaudio.__version__=}")
            logging.info(f"{pyannote.audio.__version__=}")
        
        self._whisperx_cfg = auto_configure_whisperx(verbose = True) # attempts to auto-detect and config WhisperX settings based on sys specs
        
        logging.info(
            f"WhisperX config has been automatically set based on current system specs!"
        )
        
        logging.info(f"Executing any manual overrides to auto-configured WhisperX model settings...")
        
        # WhisperX model size names quick ref:
        #     tiny, tiny.en
        #     base, base.en
        #     small, small.en
        #     medium, medium.en
        #     large, large-v1, large-v2, large-v3, large-v3-turbo
        #     Distilled models: distil-large-v2, distil-medium.en, distil-small.en, distil-large-v3
        
        # TODO load additional environment vars and overwrite auto-config settings as needed
        
        self._transcript = {} # should already be defaulted to None, but let's make doubly sure.
        
        ffmpeg_version = ensure_ffmpeg_installed()
        
        self._transcript["ffmpeg_version"] = ffmpeg_version
        
        # TODO ensure existence of required folders: cached_models_dir, etc
        
        if isinstance(filepath, Path):
            # already a Path object, great!
            self._filepath = filepath
        elif isinstance(filepath, str):
            # convert to Path object
            self._filepath = Path(filepath) 
        else:
            raise TypeError(f"Can't init AudioTranscriber: Invalid filepath `{filepath}`")
            
        init_end_time = time.perf_counter()  # end time for setup
        init_duration = init_end_time - init_start_time  # in secs
        init_duration_str = str(timedelta(seconds=init_duration))  # convert to stringified timedelta HH:MM:SS.mmm format

        self._execution_times["initialization"] = init_duration
        
        logging.info(
            f"Initialized new AudioTranscriber class in {init_duration_str}! Current datetime: {datetime.now()}"
        )
        
        
    def _load_model(
        self,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None
        ) -> WhisperModel:
        """
        Load the requested WhisperX ASR model.
        
        Args:
            NOTE: major WhisperX config options are left as parameters for any manual override scenarios, all default to self._whisperx_cfg settings.
            
            model_size:
                The WhisperX model size to load (e.g., "tiny", "base", "small", "medium", "large", "Distilled").
            device:
                The device to load the model on (e.g., "cpu", "cuda").
            compute_type:
                The compute type to load the model with (e.g., "int8", "int4", "gptq").
        
        """
        
        logging.info(
            f"Loading Whisper model '{model_size}' on {device} ({compute_type=})... Current datetime: {datetime.now()}"
        )
        model_load_start_time = time.perf_counter()  # start time for model loading (to measure download speed performance in online mode, and attempt to gauge the speed at which it can actually load the cached local model in offline mode)
        
        # if these params aren't specifically passed as params, just load the normal cfg
        if not model_size:
            model_size = self._whisperx_cfg.model_size
        if not device:
            device = self._whisperx_cfg.device
        if not compute_type:
            compute_type = self._whisperx_cfg.compute_type
        
        # just in case the model settings were overridden, write them to the transcript JSON, if they didn't change, no biggie
        self._transcript["whisperx_cfg"]["model_size"] = model_size
        self._transcript["whisperx_cfg"]["device"] = device
        self._transcript["whisperx_cfg"]["compute_type"] = compute_type
        self._transcript["whisperx_cfg"]["language"] = os.environ.get("INPUT_DEFAULT_LANGUAGE", None)
        self._transcript["whisperx_cfg"]["download_root"] = os.environ.get("CACHED_MODEL_DIR", "./tmp")
        
        model = whisperx.load_model(
            model_size,
            device=device,
            compute_type=compute_type,
            language=os.environ.get("INPUT_DEFAULT_LANGUAGE", None), # None will resolve to auto-detecting in first 30s of audio
            download_root=os.environ.get("CACHED_MODEL_DIR", "./tmp"), # default to a tmp dir in project root # TODO update this to data dir for project
        )
        
        model_load_end_time = time.perf_counter()
        model_load_duration = model_load_end_time - model_load_start_time
        model_load_duration_str = str(timedelta(seconds = model_load_duration))
        
        logging.info(f"WhisperX model (model_size={model_size}, device={device}, compute_type={compute_type}) loaded in {model_load_duration_str}! Current datetime: {datetime.now()}")
        
        self._execution_times["load_whisperx_model"] = model_load_duration
        
        return model


    def _load_audio_via_ffmpeg(self, filepath : str | None = None, sample_rate: int = 16_000) -> Dict:
        """
        Decode audio using ffmpeg -> numpy -> torch tensor style pipeline
        Bypasses torchcodec entirely. Excellent.
        
        Args:
            filepath:
                The path to the audio file to be decoded (default: class member var `_filepath`).
            sample_rate:
                The sample rate to decode the audio at (default: 16 kHz for pyannote.audio).
                
        Returns:
            Dict that pyannote.audio/whisperx can accept as pre-loaded audio in format:
                {'waveform': (1, N) torch.Tensor, 'sample_rate': int}
        """

        load_audio_start_time = time.perf_counter()
        
        if not filepath:
            filepath = self._filepath
            
        # first off, let's make sure we have a live copy of ffmpeg ready to go
        try:
            ffmpeg_version = ensure_ffmpeg_installed()
        except Exception as e:
            logging.error(f"\033[31m ERROR: Could not find ffmpeg: \033[0m {e}")
            raise RuntimeError(f"ffmpeg not found in path: {sys.PATH}")
        
        # don't question it, just let ffmpeg do its thing and hand it off to pytorch
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-threads",
            "0",
            "-i",
            filepath,
            "-f",
            "f32le",  # raw 32-bit float PCM, little-endian
            "-ac",
            "1",  # mono
            "-ar",
            str(sample_rate),  # resample to target rate
            "-",  # pipe to stdout
        ]

        result = subprocess.run(cmd, capture_output=True, check=True)
        audio_np = np.frombuffer(result.stdout, dtype=np.float32).copy()  # deep copy
        waveform = torch.from_numpy(audio_np).unsqueeze(0)  # (1, N)

        load_audio_end_time = time.perf_counter()
        load_audio_duration = load_audio_end_time - load_audio_start_time
        load_audio_duration_str = str(timedelta(seconds = load_audio_duration))
        
        self._execution_times["load_audio_via_ffmpeg"] = load_audio_duration
        
        return {"waveform": waveform, "sample_rate": sample_rate}
    
    
    # TODO add support for pathlib Path in filepath param, coerce type to str with pathlib.Path.resolve() or similar
    def transcribe(
        self,
        filepath: str | None = None,
        align: bool = False,
        diarize: bool = True
        ):
        """
        Perform transcription of the currently set audio file (or passed in filepath). Super-duper-mega-jumbo method. # TODO decimate me into itty bitty chunks

        This public method is responsible for the core functionality of the transcription process:
            - Processes the audio file with ffmpeg
            - Detecting the language of the audio
            - Validating the detected language
            - Performing the transcription process
            - Aligning the transcript to the audio (if enabled)
            - Diarizing the transcription (if enabled)
            - Storing the transcript with metadata information set internally (in memory, as class member) and returning it

        Args:
            filepath (str, optional): The path to the audio file to be transcribed. Defaults to class member var `_filepath`.
            align (bool, optional): Whether to perform word-level timestamp alignment on the transcript. Defaults to False.
            diarize (bool, optional): Whether to perform diarization on the transcript. Defaults to True.
            
        Raises:
            ValueError:
                If required prerequisites (e.g., file path) are missing.
        """
        
        if filepath is None:
            filepath = self._filepath
            
        if filepath is None: # TODO fix this better, this feels dirty...
            logging.error(f"Filepath is required for transcription. Please either set the audio file's filepath with `set_filepath()` or optionally can be passed directly to the `transcribe()` method.")
            raise ValueError(f"Filepath is required for transcription. Please either set the audio file's filepath with `set_filepath()` or optionally can be passed directly to the `transcribe()` method.")
        
        # checking for presence of HF API token in the main transcribe function to avoid doing it in each subfunction, # TODO rethink this, only diarization models are gated... later.
        if self._hf_token is None:
            raise ValueError("HF API token is required for downloading the gated HF models. Please set the token with `AudioTranscriber.set_hf_token(hf_token)`")
        
        logging.info(f"Beginning Transcription process on `{filepath}`... Current datetime: {datetime.now()}")
        logging.info(f"Flags on the play! Alignment: {align}, Diarization: {diarize}")
        
        transcription_start_time = time.perf_counter()

        audio_input = self._load_audio_via_ffmpeg(filepath) # bypasses torchcodec entirely, take that!

        # whisperx.transcribe() also accepts a raw numpy array (1-D float32, etc)
        audio_np = audio_input["waveform"].squeeze(0).numpy()
        
        lang = self._detect_language(filepath)
        
        # validate language is ISO 639-1 standard and supported by the model
        self._validate_language(lang)
        
        # load up the whisperx model as per config
        model = self._load_model(
            model_size = self._whisperx_cfg.model_size,
            device = self._whisperx_cfg.device,
            compute_type = self._whisperx_cfg.compute_type,
        )
        
        transcript = model.transcribe(
                audio_np,
                batch_size=self._whisperx_cfg.batch_size,
                language=lang if lang else os.environ.get("INPUT_DEFAULT_LANGUAGE", None), # None will resolve to auto-detecting in first 30s of audio # TODO cleanup env var me!
                print_progress=True, # progress bar!
            )
        
        # transcript, audio_input = self._translator(transcript, audio_input)
        
        if align:
            transcript, audio_input = self._align_transcript(transcript, audio_input)
        
        if diarize:
            transcript, audio_input = self._diarize_transcript(transcript, audio_input)
        
        transcription_end_time = time.perf_counter()
        transcription_duration = transcription_end_time - transcription_start_time
        transcription_duration_str = str(timedelta(seconds = transcription_duration))
        logging.info(
            f"Full transcription pipeline processed in {transcription_duration_str}  |  detected language: {transcript.get('language', 'unknown')}"
        )
        
        self._execution_times["transcription"] = transcription_duration

        # TODO set the transcript's metadata here!
        transcript["execution_times"] = self._execution_times
        transcript["created_at"] = datetime.now()
        transcript["input_filepath"] = filepath
        transcript["input_language"] = self._detect_language(filepath)
        transcript["output_language"] = self._transcript["language"]
        
        transcript["metrics"] = self._run_metrics_on_transcript() 
        
        # update transcript member var to fully processed transcript
        self._transcript = transcript
        
        # Return both transcript member var and raw audio_input dict (if needed for later pipeline steps)
        return transcript, audio_input
        
        
    def _align_transcript(self, transcript: dict, audio: np.ndarray):
        """Align transcript to audio for word-level timestamps."""

        logging.info(f"Beginning transcript word-level alignment process (word-level timestamps) on device: {self._whisperx_cfg.device}... Current datetime: {datetime.now()}")
        alignment_start_time = time.perf_counter()
        
        lang = transcript.get("language", None)  # defaults to None for auto-detect in first 30s of audio

        try:
            alignment_model, alignment_metadata = whisperx.load_align_model(
                language_code=lang if lang else os.environ.get("INPUT_DEFAULT_LANGUAGE", None), # None will resolve to auto-detecting in first 30s of audio
                device=self._whisperx_cfg.device,
            )

            aligned_transcript = whisperx.align(
                transcript["segments"],
                alignment_model,
                alignment_metadata,
                audio,
                self._whisperx_cfg.device,
                return_char_alignments=False,
            )
            
            transcript = aligned_transcript # abusing redefining parameter as newly aligned transcript, to pass to return

        except Exception as e:
            logging.error(
                f"\033[31m Recoverable ERROR! Alignment failed: \033[0m {e}. \nDefaulting to using unaligned output."
            )
            # letting code follow through to return the unmodified transcript, and conclude the alignment timing
        
        
        # passed the try/catch gauntlet, carry on
        alignment_end_time = time.perf_counter()
        alignment_duration = alignment_end_time - alignment_start_time
        alignment_duration_str = str(timedelta(seconds = alignment_duration))
        
        self._execution_times["alignment"] = alignment_duration
        
        logging.info(
            f"Word-level alignment process done in {alignment_duration_str}  |  detected language: {transcript.get('language', 'unknown')}"
        )
        
        return transcript, audio

    def _diarize_transcript(
        self, 
        transcript: dict,
        audio_input: dict
    ):
        """
        Assign speaker labels via pyannote.audio diarization model.
        """

        logging.info(f"Starting diarization process on device: {self._whisperx_cfg.device}... Current datetime: {datetime.now()}")
        diarization_start_time = time.perf_counter()
        
        try:
            from pyannote.audio import Pipeline

            diarize_model = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1", # TODO hardcoded for now, opt to choose model for diarization in settings, but must be compatible with whisperx model, downloadable with huggingface token (for gated models)
                token=self._hf_token,
                cache_dir=os.environ.get("CACHED_MODEL_DIR", "./tmp"), # default to a tmp dir in project root # TODO update this to data dir for project
            ).to(torch.device(self._whisperx_cfg.device))

            diarized_segments = diarize_model(audio_input) # TODO consider preload, min_speakers/max_speakers?

            transcript = whisperx.assign_word_speakers(diarized_segments, transcript)

        except Exception as e:
            logging.error(
                f"      \033[31m Recoverable ERROR: Diarization failed: \033[0m {e}. Skipping diarization..."
            )

        diarization_end_time = time.perf_counter()
        diarization_duration = diarization_end_time - diarization_start_time
        diarization_duration_str = str(timedelta(seconds = diarization_duration))
        
        self._execution_times["diarization"] = diarization_duration
        
        logging.info(
            f"Diarization process done in {diarization_duration_str}  |  detected language: {transcript.get('language', 'unknown')}"
        )
        
        return transcript, audio_input

    def set_filepath(self, filepath: str | Path):
        """
        Set or update the audio file path to be transcribed. Forces type to pathlib.Path for internal use, str elsewhere for compatibility sake

        Args:
            filepath:
                Path to the audio file (str or pathlib.Path, assumed mp4 with AAC codec, but literally anything that ffmpeg will accept should be fine).

        Raises:
            TypeError:
                If the provided filepath is not a supported type.
        """
        if not filepath:
            raise ValueError("Filepath is required for transcription. Please either set the audio file's filepath with `set_filepath()` or optionally can be passed directly to the `transcribe()` method.")
        
        if isinstance(filepath, "Path"):
            self._filepath = filepath
        elif isinstance(filepath, "str"):
            self._filepath = Path(filepath)
        else:
            raise TypeError(f"Invalid filepath: `{filepath}`")
    
    def _detect_language(self, filepath: str | None = None) -> str:
        """
        This method will analyze the audio content and return a language identifier code string (see ISO 639-1 language code documentation for more details).

        Args:
            filepath:
                The path to the audio file to be analyzed (default: class member var `_filepath`).
        Returns:
            A string representing the detected language code (when possible). See ISO 639-1 language code documentation for more details
        """
        
        if not filepath:
            filepath = self._filepath
        
        if not filepath:
            logging.error(f"Filepath is required for language detection. Please either set the audio file's filepath with `set_filepath()` or optionally can be passed directly to the `detect_language()` method.")
            raise ValueError(f"Filepath is required for language detection. Please either set the audio file's filepath with `set_filepath()` or optionally can be passed directly to the `detect_language()` method.")
        
        # pass the filepath to an audio language detection library
        # lang_detector = AudioLanguageDetector(filepath) # TODO implement me!
        
        try:
            # lang = lang_detector.detect_language(filepath)
            lang = "en"
        except:
            # pass it on
            raise ValueError(f"Failed to detect language in {filepath}.")
        
        return lang
    

    def to_json_file(self, output_path: str | Path = Path("transcript.json"), indent: int = 2):
        """
        Save the current transcript to a JSON file (defaults to cwd json file).
        WARNING: This method will overwrite any existing file at the specified path.
        
        Args:
            output_path:
                The name of the output JSON file.
                Defaults to "transcript.json".
            indent:
                Number of spaces to use for JSON indentation. Default: 2

        Raises:
            ValueError:
                If transcription has not yet been performed.
            IOError:
                If the file cannot be written.  
        """
        
        if not self._transcript:
            raise ValueError(f"Failed trying to output to JSON file `{output_path}`: Transcription has not yet been performed.")
        
        if isinstance(output_path, "Path"):
            # already a Path object, great!
            pass  
            
        elif isinstance(output_path, "str"):
            # convert to Path object
            output_path = Path(output_path)
            
        else:
            raise TypeError(f"Failed trying to output to JSON file `{output_path}`: Invalid filepath: `{output_path}`")
        
        # let's ensure it exists, and if not, mkdir the structure for it
        if not output_path.exists():
            output_path.mkdir(exist_ok=True)
        
        # dump the JSON out to file
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(self._transcript, f, ensure_ascii=False, indent=indent)
            
        return str(output_path.resolve()) # convert back to str for compatibility
            
    
    def to_json(self, indent: int = 2):
        """
        Format the transcript as JSON/Dict, for printing or saving to raw file.

        Args:
            indent:
                Number of spaces to use for JSON indentation.

        Returns:
            A formatted JSON representing the transcript.

        Raises:
            ValueError:
                If transcription has not yet been performed.
        """
        
        if not self._transcript:
            raise ValueError(f"Failed trying to output to JSON: Transcription has not been performed yet.")
        
        return json.dumps(self._transcript, ensure_ascii=False, indent=indent) # note the 's' in json.dumpS vs json.dump above, difference in param count, dump takes a file handle
    
    def _build_transcript_text(
        self,
        transcript: Dict
        ) -> str:
        """
        Render speaker segments to a readable plain-text transcript. # TODO modify me per format desired!
        Default format per line:
            [HH:MM:SS.mmm --> HH:MM:SS.mmm]  (SPEAKER_XX)  text
        """

        lines = []
        
        # TODO write out metadata header to text file, format tbd...
        # append directly into lines list
        

        for seg in transcript.get("segments", []):
            start = format_timestamp(seg.get("start", 0.0))
            end = format_timestamp(seg.get("end", 0.0))
            text = seg.get("text", "").strip()
            speaker = seg.get("speaker", "")
            speaker_tag = f"  [{speaker}]" if speaker else ""

            lines.append(f"[{start} --> {end}]{speaker_tag}  {text}")

        return "\n".join(lines)

    def to_text_file(self, output_path: str) -> str:
        """
        Write formatted transcript to a text file.
        """

        logging.info(f"Writing transcript to text file `{output_path}`...")
        
        if not self._transcript:
            raise ValueError(f"Failed trying to output to text file `{output_path}`: Transcription has not yet been performed.")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self._build_transcript_text(self._transcript))
            f.write("\n")  # trailing newline
        
        logging.info(f"Completed writing transcript to text file `{output_path}`.")
        
        return output_path

    def enable_online_mode(self):
        """Enable online mode."""
        logging.info(f"Online mode enabled!")
        logging.info(f"If this is an inaugural run, models will be downloaded as needed, so grab a drink and some popcorn, it may be a little while!")
        
        os.environ["HF_HUB_OFFLINE"] = "0"
        os.environ["HF_DATASETS_OFFLINE"] = "0"
        os.environ["TRANSFORMERS_OFFLINE"] = "0"
        
        self._online_mode = True
        
    def enable_offline_mode(self):
        """Enable offline mode."""
        logging.info(f"Offline mode enabled!")
        logging.info(f"In the case of running in offline mode and a model not being found in the cached model directory, load functions will throw either `OfflineModeIsEnabled` or general `OSError` exceptions.")
        
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["HF_DATASETS_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        
        self._online_mode = False
        
    def set_hf_token(self, hf_token: str):
        """Set the HuggingFace token for downloading gated models."""
        self._hf_token = hf_token
        logging.info(f"HuggingFace token set to `REDACTED`.")
        
    def assign_speaker_name(
        self,
        speaker_id: str,
        speaker_name: str,
        transcript = None
    ):
        """
        Assign a speaker name to a specific speaker ID.
        
        Args:
            transcript:
                The transcript to assign the speaker name to. Defaults to member variable `_transcript`.
            speaker_id:
                The ID of the speaker to assign the name to. ie. "1"
            speaker_name:
                The name to assign to the speaker. ie. "John Doe"
        """
        if not transcript:
            transcript = self._transcript # default to previously set if not passed as an override param
        
        if not transcript:
            raise ValueError(f"Failed trying to assign speaker label: Transcription has not yet been performed.")
        
        if not speaker_id:
            raise ValueError(f"Failed trying to assign speaker label: Speaker ID is required.")
        
        if not speaker_name:
            raise ValueError(f"Failed trying to assign speaker label: Speaker name is required.")
        
        # find the speaker in the transcript
        speakers = transcript.get("speakers", [])
        speakers.set(speaker_id, speaker_name) # TODO verify this actually works as is
        # for speaker in speakers:
        #     if speaker["id"] == speaker_id:
        #         speaker["label"] = speaker_name
        #         break
        
    def _add_model_config_to_transcript(self):
        """
        Add extra metadata about model cfg to transcript.
        """
        self._transcript["whisperx_cfg"] = self._whisperx_cfg.to_dict()
        self._transcript["execution_times"] = self._execution_times
        self._transcript["online_mode"] = "online" if self._online_mode else "cached/offline"
        
        # TODO add other config info, execution times, etc
    
    def _validate_language(self, lang_code: str):
        """
        Validate the language code is ISO 639-1 standard and supported by the model.
        
        Args:
            language:
                The language code to validate (2-character ISO 639-1 code, ie. "en")
        """
        # hand assemble the list of ISO 639-1 2-char lang codes from iso639 package:
        valid_iso_639_1_lang_codes = []
        for lang in iter_langs():
            if lang.pt1 != "": # some languages that are supported by the ISO 639 standard don't actually have 2-char ISO 639-1 codes
                valid_iso_639_1_lang_codes.append(lang.pt1)
                
        whisperx_supported_torch_alignment_lang_codes = ["en", "fr", "de", "es", "it"]
        whisperx_supported_hf_alignment_lang_codes = ["ja", "zh", "nl", "uk", "pt", "ar", "cs", "ru", "pl", "hu", "fi", "fa", "el", "tr", "da", "he", "vi", "ko", "ur", "te", "hi", "ca", "ml", "no", "nn"]
        
        whisperx_supported_lang_codes = whisperx_supported_torch_alignment_lang_codes + whisperx_supported_hf_alignment_lang_codes
        
        
        if lang_code in valid_iso_639_1_lang_codes:
            logging.info(f"Language code `{lang_code}` is valid by the ISO 639-1 standard.")
        else:
            logging.error(f"Language code `{lang_code}` is not valid by ISO 639-1 standard.")
            raise ValueError(f"Language code `{lang_code}` is not valid by ISO 639-1 standard.")
        
        if lang_code not in whisperx_supported_lang_codes:
            logging.error(f"There is no default alignment model set for this language ({lang_code}).\nA wav2vec2.0 model finetuned on this language on `https://huggingface.co/models` will be required to process this language with WhisperX.")
            raise ValueError(f"There is no default alignment model set for this language ({lang_code}).\nA wav2vec2.0 model finetuned on this language on `https://huggingface.co/models` will be required to process this language with WhisperX.")
        else:
            logging.info(f"There is a default alignment model set in WhisperX for this lang_code: ({lang_code}). Great success!")
         
        # TODO add any more language checks here   
        return True
    
    def _run_metrics_on_transcript(self):
        """
        Run metrics on the transcript and aggregate in the JSON.
        
        Returns:
            Dict of metrics and their values
        """
        
        # first, we'll calculate...
        pass