import json

with open('lm/conversation.json', 'r') as f:
    transcript = json.load(f)

text = ""
for reply in transcript["conversation"]["transcript"]:
    text = text + reply["speaker"] + ": " + reply["content"] + "\n"

print(text)