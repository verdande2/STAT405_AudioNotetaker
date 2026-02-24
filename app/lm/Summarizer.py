"""
dummy summarizer class
"""
from __future__ import annotations

from pathlib import Path
from llama_cpp import Llama
from langchain_text_splitters import RecursiveJsonSplitter
import json



class Summary:
    def __init__(self, path: str | None = None):
        """
        Args:   filesystem path to the gguf model file. If None the
                code will look for a default model in the models/
                directory (currently Qwen3-4B-Q5_0.gguf).
        """
        # default location.
        default_path = Path("models/Qwen3-4B-Q5_0.gguf")

        if path is None:
            path = str(default_path)

        if not Path(path).exists():
            raise FileNotFoundError(
                f"Summarizer model not found at '{path}'.\n"
                "Please download the Qwen3-4B-Q5_0.gguf model and either pass ``path`` "
                "explicitly or place it in the ``models/`` directory."
            )

        self.splitter = RecursiveJsonSplitter(max_chunk_size=2000, min_chunk_size=1000)
        self.llm = Llama(
            model_path=path,
            n_batch= 2048,
            n_context = 2048, #change max context size, default 2048
        )
    
    def SummarizeSingle(self, transcript, temp: float = 0.5) -> str:
        """Returns a plain text summary"""
        chunks = self.splitter.split_json(json_data=transcript, convert_lists=True)
        chunk_summaries: list[str] = []

        for chunk in chunks:
            # produce a short per-chunk summary focused on clinical content
            prompt = (
                "You are a clinical summarizer. For the following excerpt of a therapy "
                "session, write a concise 2-3 sentence summary that focuses on the "
                "patient's presenting problems, emotional state, and any coping "
                "strategies mentioned. Be factual and neutral.\n\n"
            )
            for reply in chunk.values():
                prompt += f"{reply['speaker']}: {reply['text']}\n"

            # instruct the model to produce a short neutral summary and
            # to avoid any meta commentary or internal process text
            prompt += "\nPlease provide only a concise 2-3 sentence summary. "
            prompt += "Do not include meta-comments like 'let me condense' or numbered lists. "
            prompt += "Return plain text only.\n\n"

            out = self.llm(prompt, temperature=temp, max_tokens=150)
            text_out = out.get("choices", [{}])[0].get("text", "").strip()
            if text_out:
                chunk_summaries.append(text_out)

        # final consolidation prompt: ask for a single coherent summary
        final_prompt = (
            "You are a clinical summarizer. Combine the following short summaries "
            "into one coherent 5-8 sentence summary that highlights: the main "
            "presenting problem, likely triggers, observed patterns/behaviors, "
            "and practical next-step suggestions for the clinician. Keep it "
            "clear and concise.\n\n"
        )
        for s in chunk_summaries:
            final_prompt += s + "\n"

        # final instruction: 2-3 sentences, no commentary, plain text
        final_prompt += "\nPlease return only a concise 2-3 sentence summary. "
        final_prompt += "Do not include internal reasoning, notes to self, or numbered steps. "
        final_prompt += "Return plain text only.\n\n"

        final_out = self.llm(final_prompt, temperature=temp, max_tokens=400)
        final_text = final_out.get("choices", [{}])[0].get("text", "").strip()

        # return plain text for easy logging/consumption by the UI
        return final_text


##########################################################################Bullshit
# with open('app/lm/testing/sample documents/example1.json', 'r') as f:
#     transcript = json.load(f)
#
# # explicit path
# # summary = Summary(path='~/Downloads/Qwen3-4B-Q5_0.gguf')
#
# # or rely on the default
# # summary = Summary()
#
# sum = summary.SummarizeSingle(transcript=transcript)
# print(sum)

