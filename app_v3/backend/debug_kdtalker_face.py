#!/usr/bin/env python3
"""
KDTalker debugging script with proper face image
"""
from gradio_client import Client, handle_file
from dotenv import load_dotenv
import os
import shutil

# Load environment variables
load_dotenv()

# Get HF token from environment
hf_token = os.getenv('HF_API_TOKEN')
if not hf_token:
    raise ValueError("HF_API_TOKEN not found in environment variables")

print("Initializing KDTalker client...")
client = Client("hants/KDTalker", hf_token=hf_token)

# Use a proper face image instead of a bus
# This is a sample face image that should work with face detection
try:
    print("Testing KDTalker with face image and local audio file...")
    result = client.predict(
        upload_driven_audio=handle_file('/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend/test_files/voice_joelsaltz.wav'),
        tts_driven_audio=None,  # Set to None since we're using upload audio
        driven_audio_type="upload",
        source_image=handle_file('test_files/hants.png'),  # Local face image
        smoothed_pitch=0.8,
        smoothed_yaw=0.8,
        smoothed_roll=0.8,
        smoothed_t=0.8,
        api_name="/generate"
    )
    print("Success!")
    print(f"Result: {result}")
    
    # Save the output video to test_files folder
    if result and 'video' in result and result['video']:
        video_path = result['video']
        output_path = 'test_files/output_test.mp4'
        
        print(f"Copying video from {video_path} to {output_path}")
        try:
            # Copy the video file to our desired location
            shutil.copy2(video_path, output_path)
            print(f"✅ Video saved successfully to: {output_path}")
            
            # Get file size for confirmation
            file_size = os.path.getsize(output_path)
            print(f"📁 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            
        except Exception as copy_error:
            print(f"❌ Error copying video: {copy_error}")
    else:
        print("❌ No video output received from KDTalker")
    
except Exception as e:
    print(f"Error occurred: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Try with a different face image
    print("\nTrying with a different approach...")
    try:
        # Let's try with a local image or different URL
        result = client.predict(
            upload_driven_audio=handle_file('/Users/hantswilliams/Development/python/digitalclone-iitg/app_v3/backend/test_files/voice_joelsaltz.wav'),
            tts_driven_audio=None,
            driven_audio_type="upload", 
            source_image=handle_file('test_files/hants.png'),  # Local face image
            smoothed_pitch=0.8,
            smoothed_yaw=0.8,
            smoothed_roll=0.8,
            smoothed_t=0.8,
            api_name="/generate"
        )
        print("Success with alternative image!")
        print(f"Result: {result}")
        
        # Save the output video to test_files folder
        if result and 'video' in result and result['video']:
            video_path = result['video']
            output_path = 'test_files/output_test.mp4'
            
            print(f"Copying video from {video_path} to {output_path}")
            try:
                # Copy the video file to our desired location
                shutil.copy2(video_path, output_path)
                print(f"✅ Video saved successfully to: {output_path}")
                
                # Get file size for confirmation
                file_size = os.path.getsize(output_path)
                print(f"📁 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                
            except Exception as copy_error:
                print(f"❌ Error copying video: {copy_error}")
        else:
            print("❌ No video output received from KDTalker")
        
    except Exception as e2:
        print(f"Second attempt also failed: {e2}")
        print("The KDTalker space might be having issues or the image format is not supported.")
        
        # Let's check what files are available in the current directory
        print("\nLet's try to check available test images...")
        current_dir = os.getcwd()
        print(f"Current directory: {current_dir}")
        
        # Check if we have any image files locally
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        for file in os.listdir(current_dir):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                print(f"Found local image: {file}")
