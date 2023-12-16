from gradio_client import Client
from dotenv import load_dotenv
import os
import base64
import requests 
from time import sleep

load_dotenv()

api_key = os.getenv("HUGGING")

def encode_file_to_base64(filepath):
    with open(filepath, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')
    
def encode_url_to_base64(url):
    response = requests.get(url)
    return base64.b64encode(response.content).decode('utf-8')

# Encode your image and audio files
image_base64 = encode_file_to_base64("tests/test_content/hants-open.png")
audio_base64 = encode_file_to_base64("tests/playht_outputs/playHT_ex1.wav")

# Encode your image and audio files from a URL
image_base64 = encode_url_to_base64("https://iitg-mvp.s3.amazonaws.com/sadtalker_input.png")    #("https://github.com/hantswilliams/digitalclone-iitg/blob/6c19631d76ea74a37e85011bb24f963c28d7be0d/tests/test_content/hants-open.png" + "?raw=true")
audio_base64 = encode_url_to_base64("https://github.com/hantswilliams/digitalclone-iitg/blob/973f55e45baff8f1b06a388890aac029ac7f36ad/tests/playht_outputs/playHT_ex1.wav" + "?raw=true")   # ("https://peregrine-results.s3.amazonaws.com/pigeon/Dj2kJIPvRdPZfUdVmK_0.mp3") 

# ## save the base64 string to a file
# with open("tests/gradio_sadtalker/image_base64.txt", "w") as f:
#     f.write(image_base64)

# ## save the base64 string to a file
# with open("tests/gradio_sadtalker/audio_base64.txt", "w") as f:
#     f.write(audio_base64)

# # get the first 25 charcters of the base64 string
# image_base64[:100]
# # get the last 25 characters of the base64 string
# image_base64[-25:]
# # get the first 100 characters of the base64 string
# audio_base64[:100]

client = Client(
    # src = "https://hants-sadtalker.hf.space/", 
    src = "hants/SadTalker", # this is the space name, not the full URL
    hf_token = api_key,
    output_dir="/Users/hantswilliams/Development/python/digitalclone-iitg/tests/gradio_sadtalker/"
)


### using requests 
url = "https://hants-sadtalker.hf.space/run/generate_video"
headers = {
    'Authorization': 'Bearer ' + api_key,
}
json_data = {
    "data": [
        None, # this is for the input from the form for image (user upload, not used here)  
        None, # this is for the input from the form for the audio (user upload, not used here)
        image_base64, # this is the base64 string for the image, used here
		audio_base64, # this is the base64 string for the audio, used here
		"resize", # this is the image processing method, used here (crop, resize, etc...)
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
		"/generate_video",
	]
}
response = requests.post(url, headers=headers, json=json_data)
response.text

## can use predict or client.submit

result = client.predict(
        None, # this is for the input from the form for image (user upload, not used here)  
        None, # this is for the input from the form for the audio (user upload, not used here)
        image_base64, # this is the base64 string for the image, used here
		audio_base64, # this is the base64 string for the audio, used here
		"resize", # this is the image processing method, used here (crop, resize, etc...)
		True,
		True,
		3,
		512, # this needs to be a NUBMER ! 
		0,
		"facevid2vid",
		1,
		# False,
		# None,
		# "pose",
		False,
		5,
		True,
        api_name="/generate_video",
)

print(result)

## get working jobs
# https://huggingface.co/spaces/hants/SadTalker/jobs?status=running

## get job status


job = client.submit(
        None, # this is for the input from the form for image (user upload, not used here)  
        None, # this is for the input from the form for the audio (user upload, not used here)
        image_base64, # this is the base64 string for the image, used here
		audio_base64, # this is the base64 string for the audio, used here
		"resize", # this is the image processing method, used here (crop, resize, etc...)
		True,
		True,
		3,
		512, # this needs to be a NUBMER ! 
		0,
		"facevid2vid",
		1,
		# False,
		# None,
		# "pose",
		False,
		5,
		True,
		api_name="/generate_video",
)

job.status()
job.status().code

# print job status until it is complete
while str(job.status().code) == "Status.PROCESSING":
	job_status = str(job.status().code)
	print(job_status)
	if job_status == "Status.FINISHED":
		break
	sleep(1)
     






