import os
from gradio_client import Client, handle_file

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get HF token from environment
hf_token = os.getenv('HF_API_TOKEN')
if not hf_token:
    raise ValueError("HF_API_TOKEN not found in environment variables")

client = Client("hants/IndexTTS", hf_token=hf_token)

result = client.predict(
		prompt=handle_file('https://github.com/hantswilliams/digitalclone-iitg/raw/302979c15d7bb9d625dac997d68509bd1c9321c6/app_v3/backend/test_files/voice.wav'),
		text="My name is Bobby. I am a software engineer.",
		api_name="/gen_single"
)

print(result)