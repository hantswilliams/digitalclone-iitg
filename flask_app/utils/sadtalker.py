from gradio_client import Client
from dotenv import load_dotenv
import os
import base64
import requests 
from utils.s3 import s3_upload_video

load_dotenv()

api_key = os.getenv("HUGGING")

def encode_file_to_base64(filepath):
    with open(filepath, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')
    
def encode_url_to_base64(url):
    response = requests.get(url)
    return base64.b64encode(response.content).decode('utf-8')

def create_video(image_url, audio_url):

    print('Image URL: ', image_url)
    print('audio_url: ', audio_url)

    # # Encode your image and audio files from a URL
    image_base64 = encode_url_to_base64(image_url) # have only tested succesfully with png, need to test with jpg/jpeg etc... ("https://github.com/hantswilliams/digitalclone-iitg/blob/6c19631d76ea74a37e85011bb24f963c28d7be0d/tests/test_content/hants-open.png" + "?raw=true")
    audio_base64 = encode_url_to_base64(audio_url) # strange behavior, need to make sure its a .wav, it looks like mp4 from playHT but because of config its actuall a wav. very confusing   # ("https://github.com/hantswilliams/digitalclone-iitg/blob/973f55e45baff8f1b06a388890aac029ac7f36ad/tests/playht_outputs/playHT_ex1.wav" + "?raw=true")

    print('API Key: ', api_key)

    try:
        client = Client(
            src = "https://hants-sadtalker.hf.space/", 
            hf_token = api_key,
            output_dir="/Users/hantswilliams/Development/python/digitalclone-iitg/flask_app/temp_outputs/"
        )
    except Exception as e:
        print(f"Error: {e}")
        return None

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

    ## get working directory
    working_dir = os.getcwd()
    print('WORKING DIR: ', working_dir)

    ## get the new folder name from the temp_outputs folder
    folder = os.listdir("./temp_outputs")

    ## get only the folders that exist in the temp_outputs folder
    folders = [f for f in folder if os.path.isdir(os.path.join("./temp_outputs", f))]
        
    ## get the folder name
    folder_name = folders[0]
    # print('FOLDER NAME: ', folder_name)
    
    ## get the .mp4 file from the folder
    video_file = os.listdir("./temp_outputs/" + folder_name)[0]
    
    ## upload the video file to S3
    try:
        video_url = s3_upload_video(video_file, "temp_outputs/" + folder_name + "/" + video_file)
        print('Succesfully uploaded video from: ', video_url)
        ## then delete the folder
        os.system("rm -rf temp_outputs/" + folder_name)
        print(f"Deleted folder {folder_name}")
        return f'Uploaded {video_file} to S3 bucket'
    
    except Exception as e:
        print(f"Error: {e}")
        return None




def create_video_job(image_url, audio_url):

    print('Image URL: ', image_url)
    print('audio_url: ', audio_url)

    # # Encode your image and audio files from a URL
    image_base64 = encode_url_to_base64(image_url) # have only tested succesfully with png, need to test with jpg/jpeg etc... ("https://github.com/hantswilliams/digitalclone-iitg/blob/6c19631d76ea74a37e85011bb24f963c28d7be0d/tests/test_content/hants-open.png" + "?raw=true")
    audio_base64 = encode_url_to_base64(audio_url) # strange behavior, need to make sure its a .wav, it looks like mp4 from playHT but because of config its actuall a wav. very confusing   # ("https://github.com/hantswilliams/digitalclone-iitg/blob/973f55e45baff8f1b06a388890aac029ac7f36ad/tests/playht_outputs/playHT_ex1.wav" + "?raw=true")

    print('API Key: ', api_key)

    try:
        client = Client(
            src = "https://hants-sadtalker.hf.space/", 
            hf_token = api_key,
            output_dir="/Users/hantswilliams/Development/python/digitalclone-iitg/flask_app/temp_outputs/"
        )
    except Exception as e:
        print(f"Error: {e}")
        return None

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

    print(job)

    return job
    