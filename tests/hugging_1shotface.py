# pip3 install gradio_client

from gradio_client import Client
from dotenv import load_dotenv
import os

load_dotenv()

bark_api = os.getenv("HUGGING")


client = Client(
    src = "https://hants-bark.hf.space/", 
    hf_token = bark_api,
    output_dir="/Users/hantswilliams/Development/python/digitalclone-iitg/tests/gradio_outputs/"
)