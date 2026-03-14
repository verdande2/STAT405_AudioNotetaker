"""
dummy summarizer class
"""
from llama_cpp import Llama
from langchain_text_splitters import RecursiveJsonSplitter

class Summary:
    def __init__(self, path):
        self.max_context = 4096
        # if os.path.isfile("models/Qwen3-4B-Instruct-2507-UD-IQ1_S.gguf") == False:
        #     joblib.load(
        #         hf_hub_download(repo_id="unsloth/Qwen3-4B-Instruct-2507-GGUF", filename="Qwen3-4B-Instruct-2507-UD-IQ1_S.gguf", local_dir="models/Qwen3-4B-Instruct-2507-UD-IQ1_S.gguf")
        #     )
        self.splitter = RecursiveJsonSplitter(max_chunk_size=self.max_context*3, min_chunk_size=(self.max_context*3)-2000)
        self.llm = Llama(
            model_path=path,
            n_batch= 512,
            n_ctx= self.max_context, #change max context size, default 2048
            verbose=True
        )
    
    def SummarizeSingle(self, transcript, temp = 0.6, top_k = 20, top_p = 0.7, repeat_penalty = 1.2):
        chunks = self.splitter.split_json(json_data=transcript, convert_lists=True)
        num_chunks = len(chunks)
        if num_chunks > 1:
            summaries = []
            for chunk in chunks:
                text = "The text below is a section of a transcript of a therapy session. 1. State the patient's primary concern in this session.\n 2. Summarize all of the patient's symptoms.\n 3. State the prescribed actions from the psychologist, then stop\n Then, stop. Do not add any additional thoughts, explanations, or elaborations. Do not make up information. Do not go beyond the points listed above. \n ```\n"
                for reply in chunk.values():
                    text = text + reply["speaker"] + ": " + reply["text"] + "\n "
                text = text + "\n```\n"
                output = self.llm(text, temperature=temp, top_k = top_k, top_p = top_p, repeat_penalty=repeat_penalty, max_tokens=512) # set max tokens to an amount divisible by amount we want
                print(output["choices"][0]["text"])
                summaries.append(output["choices"][0]["text"])
            text = "The text below is a group of summaries from a therapy session. 1. State the patient's primary concern in this session.\n 2. Summarize all of the patient's symptoms.\n 3. State the prescribed actions from the psychologist, then stop\n Then, stop. Do not add any additional thoughts, explanations, or elaborations. Do not make up information. Do not go beyond the points listed above. \n  "
            for sum in summaries:
                text = text + sum
            totalOutput = self.llm(text,  temperature=temp, top_k = top_k, top_p = top_p, repeat_penalty=repeat_penalty, max_tokens=512)#fix max tokens
            print(totalOutput["choices"][0]["text"])
        else:
            text = "The text below is a transcript of a therapy session. 1. State the patient's primary concern in this session.\n 2. Summarize all of the patient's symptoms.\n 3. State the prescribed actions from the psychologist, then stop\n Then, stop. Do not add any additional thoughts, explanations, or elaborations. Do not make up information. Do not go beyond the points listed above.\n ```\n"
            for reply in chunks[0].values():
                text = text + reply["speaker"] + ": " + reply["text"] + "\n "
            text = text + "\n```"
            totalOutput = self.llm(text,  temperature=temp, top_k = top_k, top_p = top_p, repeat_penalty=repeat_penalty, max_tokens=512)#fix max tokens
            print(totalOutput["choices"][0]["text"])
            
        return (totalOutput["choices"][0]["text"])