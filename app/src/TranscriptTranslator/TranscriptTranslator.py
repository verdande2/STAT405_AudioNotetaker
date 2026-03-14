from pathlib import Path
from typing import Union, Optional, Dict, Any
import json
import copy

# TODO implement these types in the code!
# type JSONVal = None | bool | str | float | int | JSONArray | JSONObject
# type JSONArray = list[JSONVal]
# type JSONObject = dict[str, JSONVal]


# TODO make me work!

class TranscriptTranslator:
    """
    A utility class for translating transcript data stored in a structured JSON format.

    The class supports loading transcript data from:
        - A file path (str or Path) pointing to a JSON file
        - A raw JSON/Dict object from json package

    Translation is applied to the "text" fields within transcript "segments", while preserving the original structure and metadata of the JSON document. See example JSON format below.

    The translated transcript can then be output to a JSON file, or returned as a JSON object in Python
    
    # example internal schema for transcript json, before any post-processing:
    {
      "metadata": {
        "language": "en", # ISO 639 language code ie. us, es, etc
        "num_speakers": 2,
        "model": "whisper-large-v3",
        #"model_version": "3.0",
        #"model_size": "large",
        "created_at": "2023-03-30T22:00:00.000Z",
        "execution_time": 0.00,
        
      },
      "speakers": [
        {"id": "SPEAKER_00", "label": "Dr. Watson"},
        {"id": "SPEAKER_01", "label": "John Doe"}
      ],
      "segments": [
        {
          "segment_id": 0,
          "speaker_id": "SPEAKER_00",
          "start": 0.00,
          "end": 3.20,
          "text": "Hello, how are you?"
        },
        {
          "segment_id": 1,
          "speaker_id": "SPEAKER_01",
          "start": 4.00,
          "end": 8.00,
          "text": "I'm good, thanks!"
        }
      ]
    }
    """

    def __init__(
        self,
        transcript_source: Optional[Union[str, Path, Dict[str, Any]]] = None, 
        input_language: Optional[str] = None, # four letter language code, ie. en-US, en-GB, etc
        output_language: Optional[str] = None, # four letter language code, ie. en-US, en-GB, etc
    ):
        """
        Initialize the TranscriptTranslator.

        Args:
            transcript_source:
                Optional source of transcript data. Can be:
                    - str or pathlib Path to a JSON file
                    - Raw JSON object
            input_language:
                Optional source language code or descriptor.
                Formatted as ISO 639-1 two-letter language code ("en"), an underscore, and a ISO 3166-1 two-letter country code ("US") like "en_US".
                For a list of language codes, see: <http://www.lingoes.net/en/translator/langcode.htm> or <https://saimana.com/list-of-country-locale-code/> for a comprehensive searchable list.
                Reference: <https://www.iso.org/iso-639-language-code> (actual standard from ISO: <https://www.iso.org/standard/74575.html>)
                Reference: <https://www.iso.org/iso-3166-country-codes.html> (actual standard from ISO: <https://www.iso.org/standard/72484.html>)
            output_language:
                Optional target language code or descriptor.
                Formatted as ISO 639-1 two-letter language code ("en"), an underscore, and a ISO 3166-1 two-letter country code ("US") like "en_US". (see `input_language` for more details about the standard.)
        """
        self._transcript_source = None
        self._transcript_data: Optional[Dict[str, Any]] = None # json object
        self._translated_data: Optional[Dict[str, Any]] = None # json object (with translated segments.text fields), generated after call to translate()

        # pass language code strings (might be None!) to "private" variables
        self._input_language: str = input_language
        self._output_language: str = output_language

        # if transcript_source is passed, pass it through to set_transcript() for processing
        if transcript_source:
            self.set_transcript(transcript_source)


    def set_transcript(self, transcript_source: Union[str, Path]) -> None:
        """
        Set or replace the current transcript source.
        WARNING: This method resets any previously generated translation.

        Args:
            transcript_source:
                The transcript input source. May be a file path (str or Path)
        """
        
        if isinstance(transcript_source, "Path"):
            self._transcript_source = transcript_source
        elif isinstance(self.transcript_source, "str"):
            self._transcript_source = Path(transcript_source)
        else:
            raise TypeError(f"Invalid filepath: `{transcript_source}`")
        
        self._transcript_data = self._load_transcript(transcript_source)

        self._translated_data = None  # Reset translation


    def _load_transcript(self, source: Union[str, Path]) -> Dict[str, Any]:
        """
        Load transcript data from a supported input format.

        Args:
            source:
                The transcript file path (str or Path)

        Returns:
            Parsed transcript data as JSON obj.

        Raises:
            ValueError:
                If the provided source type is unsupported or invalid.
        """

        if isinstance(source, Path) or (isinstance(source, str) and Path(source).exists()):
            path = Path(source)
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported transcript source path: `{source}` (type: {type(source)}).")

    
    def set_languages(self, input_language: str, output_language: str) -> None:
        """
        Set the source and target languages for translation.

        Args:
            input_language:
                Language code or descriptor representing the source language. See class docstring for more details.
            output_language:
                Language code or descriptor representing the target language. See class docstring for more details.
        """
        
        self._input_language = input_language
        self._output_language = output_language


    def translate(self) -> None:
        """
        Translate the currently loaded transcript.

        This method:
            - Translates only the "text" field of each segment
            - Stores the translated result internally in a "variable" for later retreival

        Raises:
            ValueError:
                If no transcript is loaded, or input language or output language is not set.
        """
        if not self._transcript_data:
            raise ValueError("No transcript loaded.")

        if not self._input_language:
            raise ValueError("Input language not set.")

        if not self._output_language:
            raise ValueError("Output language not set.")

        # Deep copy original to preserve original untouched, while stealing its JSON structure
        translated = copy.deepcopy(self._transcript_data)

        # pluck the segments chunk from the transcript and for each "text" field, pass it through _translate_text()
        segments = translated.get("segments", [])
        for segment in segments:
            if "text" in segment:
                original_text = segment["text"]
                segment["text"] = self._translate_text(original_text)

        # store the translated JSON in a "private" variable
        self._translated_data = translated

    def _translate_text(self, text: str) -> str:
        """
        Translate a single text segment.

        This method acts as a wrapper around an LLM-backed translator

        Args:
            text:
                The raw text string to translate.

        Returns:
            Translated text string in output_language
        """

        # --------------------------------------------------------------
        # DUMMY LLM CALL SECTION (MOCK IMPLEMENTATION)
        # --------------------------------------------------------------
        translated_text = self._llm_translate(
            text=text,
            source_lang=self._input_language,
            target_lang=self._output_language
        )
        # --------------------------------------------------------------

        return translated_text

    def _llm_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Mock implementation of an LLM-based translation call.

        This method simulates interaction with an external
        translation service or large language model. It should be
        replaced with an actual API call in production use.

        Args:
            text:
                Text to translate.
            source_lang:
                Source language identifier.
            target_lang:
                Target language identifier.

        Returns:
            Mock translated string.
        """
        
        # TODO implement me!
        
        # placeholder 
        return f"[{target_lang} translation of '{text}']"


    def get_translated_transcript(self) -> Dict[str, Any]:
        """
        Retrieve the translated transcript as a JSON object.

        Returns:
            The translated transcript JSON.

        Raises:
            ValueError:
                If translation has not yet been performed.
        """
        if not self._translated_data:
            raise ValueError("Translation has not been performed yet.")
        return self._translated_data

    def to_json(self, indent: int = 2) -> str:
        """
        Format the translated transcript as JSON string, for printing or saving to raw file.

        Args:
            indent:
                Number of spaces to use for JSON indentation.

        Returns:
            A formatted JSON string representing the translated transcript.

        Raises:
            ValueError:
                If translation has not yet been performed.
        """
        
        if not self._translated_data:
            raise ValueError("Translation has not been performed yet.")
        
        return json.dumps(self._translated_data, ensure_ascii=False, indent=indent)

    def to_file(self, output_path: Union[str, Path]) -> None:
        """
        Save the translated transcript to a JSON file. Will created folder structure as needed. 
        WARNING: This method will overwrite any existing file at the destination path.

        Args:
            output_path:
                Destination file path (str or pathlib Path) where the translated transcript should be written.

        Raises:
            ValueError:
                If translation has not yet been performed.
        """
        
        if not self._translated_data:
            raise ValueError("Translation has not been performed yet.")

        output_path = Path(output_path)
        
        # dump the JSON out to file
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(self._translated_data, f, ensure_ascii=False, indent=2)



# example internal schema for transcript result, before any post-processing:
# {
#   "metadata": {
#     "language": "en",
#     "num_speakers": 2,
#     "model": "whisper-large-v3",
#     #"model_version": "3.0",
#     #"model_size": "large",
#     "created_at": "2023-03-30T22:00:00.000Z",
#     "execution_time": 0.00,
    
#   },
#   "speakers": [
#     {"id": "SPEAKER_00", "label": "Dr. Watson"},
#     {"id": "SPEAKER_01", "label": "John Doe"}
#   ],
#   "segments": [
#     {
#       "segment_id": 0,
#       "speaker_id": "SPEAKER_00",
#       "start": 0.00,
#       "end": 3.20,
#       "text": "Hello, how are you?"
#     },
#     {
#       "segment_id": 1,
#       "speaker_id": "SPEAKER_01",
#       "start": 4.00,
#       "end": 8.00,
#       "text": "I'm good, thanks!"
#     }
#   ]
# }

