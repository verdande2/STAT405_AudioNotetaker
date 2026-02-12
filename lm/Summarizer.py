"""
dummy summarizer class
"""
from llama_cpp import Llama

class summary:
    def __init__(self): # temporarily empty, will replace the functionality of SetParameters later
        self.llm
        self.prompt_template
        # path = ""
        # model_params = 
        # model = llama_cpp.llama_load_model_from_file(...)
        # 
        
    def SetParameters(self, path): #testing class
        self.llm = Llama(
            model_path=path,
            #prompt_template = '''[INST] <<SYS>>
            #prompt template
            #<</SYS>>
            #{prompt}[/INST]
            #'''
            #n_context = 2048 change max context size
        )
        
    
    def SummarizeSingle(self, transcript):
        output = self.llm(self.prompt_template.format(prompt = transcript),
             max_tokens=150,
             echo=False,)
        return (output)
        
    def SummarizeSingleWithHistory(self, transcript, summary):
        nothing = 0