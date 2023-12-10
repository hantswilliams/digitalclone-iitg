import boto3
import os
from dotenv import load_dotenv
import requests
import io
import datetime

load_dotenv()

## set up the AWS credentials for the boto3 client
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

## connect to the AWS S3 bucket
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

## function that uploads a file to an S3 bucket, takes the file path as an argument
def s3_upload_sound(original_final_name, file_path):
    ## using io, save the audio file to working memory
    audio_response = requests.get(file_path)
    audio_file = io.BytesIO(audio_response.content) # convert to bytes object
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") #timestamp 
    final_name = f"{timestamp}_{str(original_final_name)}.mp3" # add timestamp to filename
    bucket_name='iitg-mvp'
    try:
        s3.upload_fileobj(audio_file, bucket_name, final_name)
        print(f"Uploaded {final_name} to {bucket_name}")
        return final_name
    except Exception as e:
        print(f"Error: {e}")
        return None
    
## function to upload .mp4 file to S3 bucket
def s3_upload_video(original_final_name, file_path):
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") #timestamp 
    final_name = f"{timestamp}_{str(original_final_name)}" # add timestamp to filename
    bucket_name='iitg-mvp'
    try:
        s3.upload_file(file_path, bucket_name, final_name)
        print(f"Uploaded {final_name} to {bucket_name}")
        return final_name
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_s3_image_urls(bucket_name):
    s3 = boto3.client('s3')
    try:
        images = s3.list_objects_v2(Bucket=bucket_name)['Contents']
        urls = [f"https://{bucket_name}.s3.amazonaws.com/{image['Key']}" for image in images]
        return urls
    except Exception as e:
        print(f"Error: {e}")
        return []

## Function that returns a list of image and sound urls from an S3 bucket
def s3_get_image_sounds():
    bucket_name='iitg-mvp'

    urls = get_s3_image_urls(bucket_name)
    try:
        urls.pop(0) # Remove the first item from the list (it's the folder name)
    except:
        pass

    # Create a img_urls list with the image urls that end in .png, .jpg, or .jpeg
    image_urls = [url for url in urls if url.endswith(('.png', '.jpg', '.jpeg'))]
    sound_urls = [url for url in urls if url.endswith(('.wav', '.mp3', '.mp4', '.ogg'))]

    return image_urls, sound_urls


## Function that deletes a file from an S3 bucket, takes the file name as an argument
def s3_delete_file(file_name):
    bucket_name='iitg-mvp'
    try:
        s3.delete_object(Bucket=bucket_name, Key=file_name)
        print(f"Deleted {file_name} from {bucket_name}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


## Function to get all .mp4 files from an S3 bucket
def s3_get_mp4_files():
    bucket_name='iitg-mvp'
    try:
        videos = s3.list_objects_v2(Bucket=bucket_name)['Contents']
        urls = [f"https://{bucket_name}.s3.amazonaws.com/{video['Key']}" for video in videos]
        mp4_urls = [url for url in urls if url.endswith(('.mp4'))]
        return mp4_urls
    except Exception as e:
        print(f"Error: {e}")
        return []