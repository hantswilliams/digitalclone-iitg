import gradio as gr
import boto3
import os
from dotenv import load_dotenv
import requests
import io
from PIL import Image
import base64

load_dotenv()

## set up the AWS credentials for the boto3 client
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

## connect to the AWS S3 bucket
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

def get_s3_image_urls(bucket_name):
    s3 = boto3.client('s3')
    try:
        images = s3.list_objects_v2(Bucket=bucket_name)['Contents']
        urls = [f"https://{bucket_name}.s3.amazonaws.com/{image['Key']}" for image in images]
        return urls
    except Exception as e:
        print(f"Error: {e}")
        return []

# Replace 'your_bucket_name' with your actual S3 bucket name
bucket_name = 'iitg-mvp'
urls = get_s3_image_urls(bucket_name)
urls.pop(0) # Remove the first item from the list (it's the folder name)

# Create a img_urls list with the image urls that end in .png, .jpg, or .jpeg
image_urls = [url for url in urls if url.endswith(('.png', '.jpg', '.jpeg'))]
sound_urls = [url for url in urls if url.endswith(('.wav', '.mp3', '.mp4', '.ogg'))]

def process_media(image_url, sound_url):
    image, sound = None, None

    if image_url:
        image_data = requests.get(image_url).content
        image = Image.open(io.BytesIO(image_data))

    if sound_url:
        sound = sound_url

    return image, sound

# Creating the Gradio interface
iface = gr.Interface(
    fn=process_media,
    inputs=[
        gr.Dropdown(choices=image_urls, label="Select an Image"), 
        gr.Dropdown(choices=sound_urls, label="Select a Sound")
        ],
    outputs=[
        gr.Image(),
        gr.Audio()
        ],
    title="IITG MVP",
)

# Launch the app
iface.launch(
    debug=True,
)