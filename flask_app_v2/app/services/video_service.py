"""
Video service for talking head generation with SadTalker
"""
import os
import base64
import requests
from flask import current_app
from gradio_client import Client
from app.services.storage_service import StorageService


class VideoService:
    """
    Service for generating talking head videos from images and audio
    Using SadTalker as the default provider, following the "LEGO Approach"
    """
    
    def __init__(self):
        """Initialize the video service with available providers"""
        self.providers = {
            'sadtalker': self._sadtalker_generate,
            # Add other providers as they become available
            # 'synctalk': self._synctalk_generate,
        }
        self.storage_service = StorageService()
    
    def generate_video(self, image_url, audio_url, provider='sadtalker', **kwargs):
        """
        Generate a talking head video from an image and audio
        
        Args:
            image_url (str): URL to the image
            audio_url (str): URL to the audio
            provider (str): Video generation provider (default: sadtalker)
            **kwargs: Additional parameters for the provider
            
        Returns:
            dict: Result containing status and video information
        """
        if provider not in self.providers:
            return {
                'success': False,
                'error': f'Provider {provider} not supported',
                'supported_providers': list(self.providers.keys())
            }
        
        return self.providers[provider](image_url, audio_url, **kwargs)
    
    def _sadtalker_generate(self, image_url, audio_url, **kwargs):
        """
        Generate video using SadTalker via Hugging Face
        
        Args:
            image_url (str): URL to the image
            audio_url (str): URL to the audio
            **kwargs: Additional parameters for SadTalker
            
        Returns:
            dict: Result containing status and video URL
        """
        # Get API credentials
        api_key = current_app.config['HUGGING_FACE_API_KEY']
        
        if not api_key:
            current_app.logger.error("Hugging Face API key not configured")
            return {
                'success': False,
                'error': 'Hugging Face API key not configured'
            }
        
        try:
            # Encode image and audio to base64
            image_base64 = self._encode_url_to_base64(image_url)
            audio_base64 = self._encode_url_to_base64(audio_url)
            
            # Set default parameters if not provided
            preprocess = kwargs.get('preprocess', 'resize')
            still_mode = kwargs.get('still_mode', True)
            use_enhancer = kwargs.get('use_enhancer', True)
            pose_style = kwargs.get('pose_style', 0)
            size = kwargs.get('size', 512)
            expression_scale = kwargs.get('expression_scale', 1)
            
            # Initialize Hugging Face client
            client = Client(
                src="https://hants-sadtalker.hf.space/",
                hf_token=api_key,
                output_dir=current_app.config['TEMP_OUTPUT_FOLDER']
            )
            
            # Generate video
            result = client.predict(
                None,  # No direct image upload
                None,  # No direct audio upload
                image_base64,
                audio_base64,
                preprocess,
                still_mode,
                use_enhancer,
                expression_scale,
                size,
                pose_style,
                api_name="/sadtalker"
            )
            
            if not result or not os.path.exists(result):
                return {
                    'success': False,
                    'error': 'Failed to generate video or result file not found'
                }
            
            # Upload video to S3
            filename = os.path.basename(result)
            s3_filename = self.storage_service.upload_video(filename, result)
            
            if not s3_filename:
                return {
                    'success': False,
                    'error': 'Failed to upload video to storage'
                }
            
            # Build URL for the uploaded video
            video_url = f"https://{current_app.config['S3_BUCKET_NAME']}.s3.amazonaws.com/{s3_filename}"
            
            return {
                'success': True,
                'local_path': result,
                'url': video_url,
                'filename': s3_filename
            }
            
        except Exception as e:
            current_app.logger.error(f"Error generating video with SadTalker: {str(e)}")
            return {
                'success': False,
                'error': f'SadTalker error: {str(e)}'
            }
    
    def _encode_url_to_base64(self, url):
        """
        Encode a file from URL to base64
        
        Args:
            url (str): URL of the file to encode
            
        Returns:
            str: Base64 encoded string
        """
        response = requests.get(url)
        if response.status_code != 200:
            raise ValueError(f"Failed to download from {url}: {response.status_code}")
        return base64.b64encode(response.content).decode('utf-8')
