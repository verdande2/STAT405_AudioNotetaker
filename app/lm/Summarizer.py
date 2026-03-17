"""
dummy summarizer class
"""
from __future__ import annotations

from pathlib import Path
from langchain_text_splitters import RecursiveJsonSplitter
import json

try:
    from llama_cpp import Llama
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "Missing optional dependency 'llama-cpp-python'. "
        "Install it with `uv sync --extra local-llm` to enable local summarization."
    ) from exc



class Summary:
    def __init__(self, path: str | None = None):
        """
        Args:   filesystem path to the gguf model file. If None the
                code will look for a default model in the models/
                directory (currently Qwen3-4B-Q5_0.gguf).
        """
        # Resolve model paths relative to the repository root so launching the
        # app from a different working directory still finds the model.
        repo_root = Path(__file__).resolve().parents[2]
        default_path = repo_root / "models" / "Qwen3-4B-Q5_0.gguf"

        if path is None:
            resolved_path = default_path
        else:
            candidate = Path(path).expanduser()
            if candidate.is_absolute():
                resolved_path = candidate
            else:
                cwd_candidate = Path.cwd() / candidate
                repo_candidate = repo_root / candidate
                if cwd_candidate.exists():
                    resolved_path = cwd_candidate
                else:
                    resolved_path = repo_candidate

        if not resolved_path.exists():
            raise FileNotFoundError(
                f"Summarizer model not found.\n"
                f"Configured path: '{path or 'models/Qwen3-4B-Q5_0.gguf'}'\n"
                f"Resolved path: '{resolved_path}'\n"
                "Please download the Qwen3-4B-Q5_0.gguf model and either pass ``path`` "
                "explicitly or place it in the ``models/`` directory."
            )

        self.splitter = RecursiveJsonSplitter(max_chunk_size=2000, min_chunk_size=1000)
        self.llm = Llama(
            model_path=str(resolved_path),
            n_batch=2048,
            n_context=8192,  # increased from 2048 — Qwen3 uses thinking tokens that eat context
        )
    
    def SummarizeSingle(self, transcript, temp: float = 0.5) -> str:
        """Returns a plain text summary"""
        chunks = self.splitter.split_json(json_data=transcript, convert_lists=True)
        chunk_summaries: list[str] = []

        for chunk in chunks:
            excerpt = "\n".join(
                f"{reply['speaker']}: {reply['text']}"
                for reply in chunk.values()
            )
            out = self.llm.create_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a clinical summarizer. Write concise, factual, neutral "
                            "clinical summaries in plain prose. Return plain text only — no "
                            "bullet points, no numbered lists, no meta-commentary. /no_think"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Summarize the following therapy session excerpt in 2-3 sentences. "
                            "Focus on the patient's presenting problems, emotional state, and "
                            "any coping strategies mentioned.\n\n"
                            + excerpt
                        ),
                    },
                ],
                temperature=temp,
                max_tokens=512,
            )
            text_out = out["choices"][0]["message"]["content"].strip()
            if text_out:
                chunk_summaries.append(text_out)

        combined = "\n".join(chunk_summaries)
        final_out = self.llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a clinical summarizer. Write concise, factual, neutral "
                        "clinical summaries in plain prose. Return plain text only — no "
                        "bullet points, no numbered lists, no meta-commentary. /no_think"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Combine the following session notes into one coherent 5-8 sentence "
                        "clinical summary. Highlight: the main presenting problem, likely "
                        "triggers, observed patterns or behaviors, and practical next-step "
                        "suggestions for the clinician.\n\n"
                        + combined
                    ),
                },
            ],
            temperature=temp,
            max_tokens=1024,
        )
        final_text = final_out["choices"][0]["message"]["content"].strip()

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

