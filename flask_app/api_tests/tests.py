import requests 
import urllib.parse
import json
from dotenv import load_dotenv
import os

load_dotenv()

playHTid = os.getenv("PLAYHT_USERID")
playHTtoken = os.getenv("PLAYHT_SECRET")

## test the /view1/text/upload at localhost:5005
## test the /view1/text/upload at localhost:5005
## test the /view1/text/upload at localhost:5005

url = "http://localhost:5005/view1/text/upload"
data = {
        "text_input": "Testing View Upload"
    }
headers={'Content-Type': 'application/x-www-form-urlencoded'}
response = requests.post(url, data=data, headers=headers)
response.json()









## test /audio/stream-data at localhost:5005 WITH OUT STREAMING
## test /audio/stream-data at localhost:5005 WITH OUT STREAMING
## test /audio/stream-data at localhost:5005 WITH OUT STREAMING

"""
CREATING AUDIO: text: Alright..., voice: male_hants, stream: True
"""

url = "http://localhost:5005/audio/stream-data"

arg1_text = "Alright we are going to do some stuff"
arg1_voice = "male_hants"
arg1_stream = "False"

# Construct the dictionary with arguments
data = {
    "text": arg1_text,
    "voice": arg1_voice,
    "stream": arg1_stream
}

# URL encode the data
encoded_data = urllib.parse.urlencode(data)

# Full URL with encoded query
full_url = f"{url}?{encoded_data}"

headers={'Content-Type': 'application/x-www-form-urlencoded'}

response = requests.post(full_url, headers=headers)
response_dict = response.json()
jobLinkstatus = response_dict['_links'][0]['href']
headers = {
    "accept": "application/json",
    "Authorization": "Bearer " + playHTtoken,
    "X-USER-ID": playHTid
}
request2 = requests.get(jobLinkstatus, headers=headers)
request2.json()




