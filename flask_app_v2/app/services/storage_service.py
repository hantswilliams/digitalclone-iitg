"""
Storage service for handling file uploads and S3 integration
"""
import os
import io
import datetime
import boto3
import requests
from flask import current_app


class StorageService:
    """Service for handling file storage operations, primarily with S3"""
    
    def __init__(self):
        """Initialize the storage service with S3 connection"""
        self.s3 = None
        self.initialize_s3()
    
    def initialize_s3(self):
        """Initialize S3 client with credentials from app config"""
        aws_access_key = current_app.config.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = current_app.config.get('AWS_SECRET_ACCESS_KEY')
        
        if aws_access_key and aws_secret_key:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
        else:
            current_app.logger.warning("AWS credentials not configured, S3 operations will fail")
    
    def ensure_s3_initialized(self):
        """Ensure S3 client is initialized before operations"""
        if not self.s3:
            self.initialize_s3()
            if not self.s3:
                raise ValueError("S3 client could not be initialized - check AWS credentials")
    
    def upload_audio(self, filename, file_path):
        """
        Upload audio file to S3 bucket
        
        Args:
            filename (str): Original filename
            file_path (str): URL or local path to the audio file
            
        Returns:
            str: S3 filename if successful, None otherwise
        """
        self.ensure_s3_initialized()
        bucket_name = current_app.config.get('S3_BUCKET_NAME', 'iitg-mvp')
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        s3_filename = f"{timestamp}_{filename}.mp3"
        
        try:
            # If file_path is a URL, download it first
            if file_path.startswith('http'):
                audio_response = requests.get(file_path)
                if audio_response.status_code != 200:
                    current_app.logger.error(f"Failed to download audio from {file_path}")
                    return None
                audio_file = io.BytesIO(audio_response.content)
                self.s3.upload_fileobj(audio_file, bucket_name, s3_filename)
            else:
                # If file_path is a local path
                self.s3.upload_file(file_path, bucket_name, s3_filename)
            
            current_app.logger.info(f"Uploaded {s3_filename} to {bucket_name}")
            return s3_filename
            
        except Exception as e:
            current_app.logger.error(f"Error uploading audio to S3: {str(e)}")
            return None
    
    def upload_video(self, filename, file_path):
        """
        Upload video file to S3 bucket
        
        Args:
            filename (str): Original filename
            file_path (str): Path to the video file
            
        Returns:
            str: S3 filename if successful, None otherwise
        """
        self.ensure_s3_initialized()
        bucket_name = current_app.config.get('S3_BUCKET_NAME', 'iitg-mvp')
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        s3_filename = f"{timestamp}_{filename}"
        
        try:
            self.s3.upload_file(file_path, bucket_name, s3_filename)
            current_app.logger.info(f"Uploaded {s3_filename} to {bucket_name}")
            return s3_filename
            
        except Exception as e:
            current_app.logger.error(f"Error uploading video to S3: {str(e)}")
            return None
    
    def upload_image(self, filename, file_path_or_data):
        """
        Upload image file to S3 bucket
        
        Args:
            filename (str): Original filename
            file_path_or_data: Path to image file or file-like object
            
        Returns:
            str: S3 filename if successful, None otherwise
        """
        self.ensure_s3_initialized()
        bucket_name = current_app.config.get('S3_BUCKET_NAME', 'iitg-mvp')
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        s3_filename = f"{timestamp}_{filename}"
        
        try:
            if isinstance(file_path_or_data, str):
                # If file_path_or_data is a file path
                self.s3.upload_file(file_path_or_data, bucket_name, s3_filename)
            else:
                # If file_path_or_data is a file-like object
                self.s3.upload_fileobj(file_path_or_data, bucket_name, s3_filename)
            
            current_app.logger.info(f"Uploaded {s3_filename} to {bucket_name}")
            return s3_filename
            
        except Exception as e:
            current_app.logger.error(f"Error uploading image to S3: {str(e)}")
            return None
    
    def upload_presentation(self, filename, file_path):
        """
        Upload presentation file to S3 bucket
        
        Args:
            filename (str): Original filename
            file_path (str): Path to the presentation file
            
        Returns:
            str: S3 filename if successful, None otherwise
        """
        self.ensure_s3_initialized()
        bucket_name = current_app.config.get('S3_BUCKET_NAME', 'iitg-mvp')
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        s3_filename = f"{timestamp}_{filename}"
        
        try:
            self.s3.upload_file(file_path, bucket_name, s3_filename)
            current_app.logger.info(f"Uploaded {s3_filename} to {bucket_name}")
            return s3_filename
            
        except Exception as e:
            current_app.logger.error(f"Error uploading presentation to S3: {str(e)}")
            return None
    
    def get_file_urls(self, file_type=None):
        """
        Get all file URLs from S3 bucket, optionally filtered by file type
        
        Args:
            file_type (str, optional): Filter by file extension
            
        Returns:
            list: List of URLs for files in the bucket
        """
        self.ensure_s3_initialized()
        bucket_name = current_app.config.get('S3_BUCKET_NAME', 'iitg-mvp')
        
        try:
            response = self.s3.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' not in response:
                return []
            
            files = response['Contents']
            
            if file_type:
                files = [f for f in files if f['Key'].lower().endswith(file_type.lower())]
            
            urls = [f"https://{bucket_name}.s3.amazonaws.com/{file['Key']}" for file in files]
            return urls
            
        except Exception as e:
            current_app.logger.error(f"Error getting files from S3: {str(e)}")
            return []
