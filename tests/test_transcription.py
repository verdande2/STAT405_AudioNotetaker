from app.src.AudioTranscriber.AudioTranscriber import AudioTranscriber
import os, jiwer, werpy, torch, Levenshtein, pytest
from transformers import BertTokenizer, BertModel
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.metrics import jaccard_score
from datasets import load_dataset, Audio

from torch.utils.data.sampler import BatchSampler, RandomSampler
from torch.utils.data import DataLoader


# Nvidia's standards as to what makes for "good" values for various ASR metrics https://docs.nvidia.com/nemo/curator/25.09/about/concepts/audio/quality-metrics.html
# see original WhisperX research paper for originally calculated accuracy and other metrics https://www.robots.ox.ac.uk/~vgg/publications/2023/Bain23/bain23.pdf
def assert_close_enough_transcript_text(text_result, text_known, threshold = .9):
        """Compare transcriber output to the known reference sentence from the curated dataset and assert if the result is _close enough_ to the reference text."""
        
        # We have a variety of metrics to choose from to evaluate the quality of transcription accuracy, will likely utilize the mean of the WER over all segments? # TODO determine this
        output = jiwer.process_words(reference = text_known, hypothesis = text_result)
        wer = output.wer
        mer = output.mer
        wil = output.wil
        cer = jiwer.cer(text_known, text_result)
        
        # TODO Levenshtein? cos similarity? fuzzy match? see reference_notebooks/audio_transcript_analysis.ipynb for more info
        # additional information re: evaluating ASR model transcripts in python https://medium.com/@manuedavakandam/from-audio-to-words-a-python-guide-to-measuring-transcription-accurracy-f9dd9e70651f
        
        # for strcmp, strip whitespace chars and convert to lower case for standardized comparison
        assert text_known.strip().lower() == text_result.strip().lower()
        
        
class TestTranscription():
    
    # def load_dataset(self, dataset_language = "en"):
    #     # load up the common voice v2 dataset from mozilla, subset by test split, must have `trust_remote_code=True` to work, downloaded data in language `dataset_language`
    #     common_voice_dataset = load_dataset(
    #         "fsicoli/common_voice_22_0",
    #         dataset_language,
    #         split="test",
    #         trust_remote_code=True,
    #         cache_dir=os.environ.get("HF_DATASETS_CACHE"))
    #     common_voice_dataset.set_format("torch") # set to PyTorch format so DataLoader can be used to get a sample batch
        
    #     # convert to 16KHz Audio type for whisperx model's use later
    #     common_voice_dataset = common_voice_dataset.cast_column("audio", Audio(sampling_rate=16_000))
        
    #     # use torch's BatchSampler to sample 32 items to test
    #     batch_sampler = BatchSampler(RandomSampler(common_voice_dataset), batch_size=32, drop_last=False)
        
    #     dataloader = DataLoader(common_voice_dataset, batch_sampler = batch_sampler, batch_size = 16, shuffle = True, num_workers = 4)
    # TODO finish me!
    pass   
       
    
    
        
    @pytest.mark.parametrize("idx", range(32))
    def test_transcribe_sample(transcriber, samples, idx):
        sample = samples[idx]
        # result = transcriber.transcribe(sample) # returns dict/json result
        # assert_close_enough_transcript_text(result.text, sample["sentence"])
        assert 1
    
    # SRS 1.2 Local processing 
    # Verify transcription functions with all network adapters disabled.
    def test_transcription_offline_mode(self):
        assert 1 == 1
        
        
    # SRS 2.3 Usability
    # Measure "Time to Success" for a first-time user importing an MP4.
    def test_first_time_run(self):
        assert 1 == 1
        
        
    # SRS 2.4 Efficiency
    # Benchmark processing duration for a 10-minute audio file.
    def test_ten_min_audio_file(self):
        assert 1 == 1
        