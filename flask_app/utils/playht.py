import requests 
import os 
from dotenv import load_dotenv
import json
import io
import datetime

load_dotenv()

userid = os.getenv("PLAYHT_USERID")
apikey = os.getenv("PLAYHT_SECRET")

voices = {
    "male_matt": "s3://voice-cloning-zero-shot/09b5c0cc-a8f4-4450-aaab-3657b9965d0b/podcaster/manifest.json",
    "female_nichole": "s3://voice-cloning-zero-shot/7c38b588-14e8-42b9-bacd-e03d1d673c3c/nicole/manifest.json"
}

def generate_voice(selected_voice, selected_text):

    print('selected_voice:', selected_voice)
    print('selected_text:', selected_text)

    url = "https://api.play.ht/api/v2/tts"
    
    payload = {
        "text": f"{str(selected_text)}",
        "voice": f"{voices[selected_voice]}",
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

    # ## using io, save the audio file to working memory
    # audio_response = requests.get(audio_url)
    # audio_file = io.BytesIO(audio_response.content)

    # ## create a timestamped filename
    # timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    # ## save the audiofile to a remote location, in this case, the tests folder
    # with open(f'tests/playht_outputs/playht_audio_{timestamp}.mp3', 'wb') as f:
    #     f.write(audio_file.getbuffer())

    return audio_url


