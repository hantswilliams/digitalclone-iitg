# pip3 install git+https://github.com/huggingface/transformers.git
# pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu

from transformers import AutoProcessor, BarkModel
import scipy
import datetime

processor = AutoProcessor.from_pretrained("suno/bark")
model = BarkModel.from_pretrained("suno/bark")

voice_preset = "v2/en_speaker_6"

inputs = processor("My name is Haunts Williams. Today we will be talking about python. Specifically - how to load packages.", voice_preset=voice_preset)

## generate
starttime = datetime.datetime.now()
audio_array = model.generate(**inputs)
audio_array = audio_array.cpu().numpy().squeeze()
endtime = datetime.datetime.now()
print("Time taken in seconds: ", (endtime - starttime).total_seconds())

## save
sample_rate = model.generation_config.sample_rate
scipy.io.wavfile.write("tests/gradio_outputs/test.wav", rate=sample_rate, data=audio_array)
