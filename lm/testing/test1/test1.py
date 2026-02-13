# import Summarizer

models = { "lm/models/granite-4.0-h-tiny", "lm/models/granite-4.0-micro", "lm/models/Qwen3-0.6B" }
transcripts = { "lm/testing/testDocuments/transcript1.txt", "lm/testing/testDocuments/transcript2.txt" }

output = "lm/testing/test1/test1Output.txt"
open(output)

summary = Summary()
template = "You summarize transcripts for medical applications. Identify the patient's main issues."

for model in models:
    summary.SetParameters(path = model, template = template)
    for transcript in transcripts:
        text = open(transcript).read()
        for i in range(8):
            output.write(model + "\n" + transcript + "\n" + i/1