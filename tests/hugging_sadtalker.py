from gradio_client import Client
from dotenv import load_dotenv
import os
import base64
import io 
import requests

load_dotenv()

api_key = os.getenv("HUGGING")

def encode_file_to_base64(filepath):
    with open(filepath, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')
    
# Define your functions here
def getbase64image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Encode your image and audio files
image_base64 = encode_file_to_base64("tests/test_content/hants-open.png")
audio_base64 = encode_file_to_base64("tests/playht_outputs/playHT_ex1.wav")

## save the base64 string to a file
with open("tests/gradio_sadtalker/image_base64.txt", "w") as f:
    f.write(image_base64)

## save the base64 string to a file
with open("tests/gradio_sadtalker/audio_base64.txt", "w") as f:
    f.write(audio_base64)

# get the first 25 charcters of the base64 string
image_base64[:100]
# get the last 25 characters of the base64 string
image_base64[-25:]
# get the first 100 characters of the base64 string
audio_base64[:100]

client = Client(
    src = "https://hants-sadtalker.hf.space/", 
    hf_token = api_key,
    output_dir="/Users/hantswilliams/Development/python/digitalclone-iitg/tests/gradio_sadtalker/"
)

result = client.predict(
        None,
        None,
        image_base64,
		audio_base64,
		"resize",
		True,
		True,
		3,
		512, # this needs to be a NUBMER ! 
		0,
		"facevid2vid",
		1,
		False,
		None,
		"pose",
		False,
		5,
		True,
)



print(result)

## get working jobs
# https://huggingface.co/spaces/hants/SadTalker/jobs?status=running

## get job status




import base64
import requests
import json

def encode_file_to_base64(filepath):
    with open(filepath, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

# Encode your image and audio files
image_base64 = encode_file_to_base64("tests/test_content/hants-open.png")
audio_base64 = encode_file_to_base64("tests/playht_outputs/playHT_ex1.wav")

# Prepare the JSON payload
payload = {
    "data": [
        '',
        '',   
        image_base64,
        audio_base64,
        "crop",  # Example
        True,   # Still mode 
        True, # Face enhancer 
        3, # batch size 
        "512", # face model resolution 
        0, # pose style 
        "facevid2vid", # face rendered component 
        1, # expression scale 
        False, # reference video 
        None, # file name 
        "pose", # reference video 
        False, # idle animation 
        5, # represent video length
        True, # use eye blink,
    ]
}

# API endpoint
api_url = "https://huggingface.co/spaces/hants/SadTalker"

# Headers
headers = {
    "authorization" : f"Bearer {api_key}",
}

# Make the POST request
response = requests.post(api_url, json=payload, headers=headers)

# Check the response
if response.status_code == 200:
    print("Successfully sent the files.")
    response_data = response.json()
    # Process the response data as needed
else:
    print("Failed to send the files. Status code:", response.status_code)
