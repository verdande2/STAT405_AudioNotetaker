"""
dummy summarizer class
"""
from llama_cpp import Llama
from langchain_text_splitters import RecursiveJsonSplitter
import json
import ctypes



class Summary:
    def __init__(self, path): # temporarily empty, will replace the functionality of SetParameters later
        self.llm = False
        self.prompt_template = False
        self.splitter = RecursiveJsonSplitter(max_chunk_size=300)
        self.llm = Llama(
            model_path=path,
            n_batch= 512,
            n_context = 512, #change max context size, default 2048
            tokenizer=(path)
        )
    
    def SummarizeSingle(self, transcript, temp = 0.2):
        chunks = self.splitter.split_json(json_data=transcript, convert_lists=True)
        summaries = []
        for chunk in chunks:
            text = ""
            for reply in chunk.values():
                text = text + reply["speaker"] + ": " + reply["text"] + "\n "
            inputText = text.encode('utf-8')
            tokens = self.llm.tokenize(text=inputText)
            outputTokens = self.llm.generate(tokens, temp=temp)
            output = self.llm.detokenize(outputTokens)
            summaries.append(output)
        
        #create output variable, change output idk man make it stink dude holy cow everyone plug they nose when u enter the dam room
        return (summaries)

##########################################################################Bullshit
with open('lm/testing/sample documents/example1.json', 'r') as f:
    transcript = json.load(f)

summary = Summary(path='lm/models/Qwen3-4B-Q4_K_M.gguf')

print(summary.SummarizeSingle(transcript=transcript))

