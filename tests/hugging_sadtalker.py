from gradio_client import Client
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("HUGGING")

client = Client(
    src = "https://hants-sadtalker.hf.space/run/generate_video", 
    hf_token = api_key,
    output_dir="/Users/hantswilliams/Development/python/digitalclone-iitg/tests/gradio_sadtalker/"
)

result = client.predict()

