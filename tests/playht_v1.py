import requests 
import os 
from dotenv import load_dotenv
import pandas as pd 
import json
import io
import datetime


load_dotenv()

userid = os.getenv("PLAYHT_USERID")
apikey = os.getenv("PLAYHT_SECRET")

########################################################################
#######################GET LIST OF VOICES###############################
########################################################################

## get list of voices
url = "https://api.play.ht/api/v2/voices"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer " + apikey,
    "X-USER-ID": userid
}
response = requests.get(url, headers=headers)
print(response.text)

## convert response to dataframe
response_df = pd.DataFrame(response.json())
response_df.to_csv('tests/playht_outputs/voices.csv')


## get cloned voices 
url = "https://api.play.ht/api/v2/cloned-voices"
headers = {
    "accept": "application/json",
    "Authorization": "Bearer " + apikey,
    "X-USER-ID": userid
}
response = requests.get(url, headers=headers)
print(response.text)



########################################################################
#########################CREATE SOME SOUNDS#############################
########################################################################


## generate some audio fromt text 
## using matt's voice -> s3://voice-cloning-zero-shot/09b5c0cc-a8f4-4450-aaab-3657b9965d0b/podcaster/manifest.json

url = "https://api.play.ht/api/v2/tts"
payload = {
    "text": "Alright, what we are going to do? We are going to learn python.",
    "voice": "s3://voice-cloning-zero-shot/09b5c0cc-a8f4-4450-aaab-3657b9965d0b/podcaster/manifest.json",
    "output_format": "mp3",
    "voice_engine": "PlayHT2.0"
}
headers = {
    "accept": "text/event-stream",
    "content-type": "application/json",
    "Authorization": "Bearer " + apikey,
    "X-USER-ID": userid
}

response = requests.post(url, json=payload, headers=headers)
print(response.text)

## response is stream data, lets put it in dictionary
# Initialize an empty dictionary to store the parsed data
parsed_data = {}

# Split the response text into lines
lines = response.text.split("\n")

# Iterate through the lines and parse the data
for line in lines:
    if line.startswith("data:"):
        # Extract the JSON data part
        data_json = line[len("data:"):].strip()
        # Parse the JSON and convert it into a dictionary
        data_dict = json.loads(data_json)
        
        # Extract the 'event' from the line if needed
        event = line.split("event:")[1].strip() if "event:" in line else None
        
        # Add the data to the dictionary, using the 'event' as the key if available
        if event:
            parsed_data[event] = data_dict
        else:
            # If there's no 'event', use a default key
            parsed_data["default"] = data_dict

print(parsed_data)

## get the url of the audio file
audio_url = parsed_data.get("default").get("url")

## using io, save the audio file to working memory
audio_response = requests.get(audio_url)
audio_file = io.BytesIO(audio_response.content)

## create a timestamped filename
timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

## save the audiofile to a remote location, in this case, the tests folder
with open(f'tests/playht_outputs/playht_audio_{timestamp}.mp3', 'wb') as f:
    f.write(audio_file.getbuffer())
