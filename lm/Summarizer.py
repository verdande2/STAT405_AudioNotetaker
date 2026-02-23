"""
dummy summarizer class
"""
from llama_cpp import Llama
from langchain_text_splitters import RecursiveJsonSplitter
import json



class Summary:
    def __init__(self, path): # temporarily empty, will replace the functionality of SetParameters later
        self.splitter = RecursiveJsonSplitter(max_chunk_size=2000, min_chunk_size=1000)
        self.llm = Llama(
            model_path=path,
            n_batch= 512,
            n_context = 512, #change max context size, default 2048
        )
    
    def SummarizeSingle(self, transcript, temp = 0.5):
        chunks = self.splitter.split_json(json_data=transcript, convert_lists=True)
        summaries = []
        for chunk in chunks:
            text = "The following text is a transcript from a patient meeting with a therapist. Summarize the patient's condition and the stories they tell"
            for reply in chunk.values():
                text = text + reply["speaker"] + ": " + reply["text"] + "\n "
            output = self.llm(text, temperature=temp, max_tokens=256) # set max tokens to an amount divisible by amount we want
            print(output)
            summaries.append(output)
        return (summaries)

##########################################################################Bullshit
with open('lm/testing/sample documents/example2.json', 'r') as f:
    transcript = json.load(f)

summary = Summary(path='lm/models/Phi-3-mini-4k-instruct-q4.gguf')

sum = summary.SummarizeSingle(transcript=transcript)

print(sum)

