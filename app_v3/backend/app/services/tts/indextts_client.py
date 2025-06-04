"""
IndexTTS API client for voice cloning and text-to-speech generation.

This module provides a client for the IndexTTS API using Gradio client.
Supports voice cloning from reference audio samples and text-to-speech generation.
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from io import BytesIO
from flask import current_app

try:
    from gradio_client import Client, handle_file
except ImportError:
    Client = None
    handle_file = None

try:
    from huggingface_hub import HfApi
except ImportError:
    HfApi = None

logger = logging.getLogger(__name__)


class IndexTTSAPIError(Exception):
    """Custom exception for IndexTTS API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class IndexTTSClient:
    """
    Client for IndexTTS API integration using Gradio client.
    
    Handles voice cloning and text-to-speech generation using the IndexTTS Hugging Face Space.
    """
    
    def __init__(self, hf_token: Optional[str] = None, space_name: Optional[str] = None):
        """
        Initialize the IndexTTS client.
        
        Args:
            hf_token: Hugging Face token for private spaces. If not provided, reads from config.
            space_name: Hugging Face space name. If not provided, reads from config.
        """
        if Client is None:
            raise ImportError("gradio_client package is required. Install with: pip install gradio_client")
        
        self.hf_token = hf_token or self._get_config_value('HF_TOKEN') or self._get_config_value('HF_API_TOKEN')
        self.space_name = space_name or self._get_config_value('INDEXTTS_SPACE_NAME', 'hants/IndexTTS')
        
        # Initialize HfApi for metadata fetching
        self.hf_api = None
        if HfApi:
            try:
                self.hf_api = HfApi(token=self.hf_token)
            except Exception as e:
                logger.warning(f"Failed to initialize HfApi: {str(e)}")
        else:
            logger.warning("huggingface_hub package not available for metadata fetching")
        
        if not self.hf_token:
            logger.warning("No Hugging Face token provided. This may limit access to private spaces.")
        
        # Initialize the Gradio client
        try:
            if self.hf_token:
                self.client = Client(self.space_name, hf_token=self.hf_token)
            else:
                self.client = Client(self.space_name)
            
            logger.info(f"Initialized IndexTTS client with space: {self.space_name}")
        except Exception as e:
            raise IndexTTSAPIError(f"Failed to initialize IndexTTS client: {str(e)}")
    
    def _get_config_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value from Flask config or environment."""
        try:
            # Try to get from Flask config first
            return getattr(current_app.config, key, None) or os.environ.get(key, default)
        except RuntimeError:
            # Not in Flask context, use environment variable
            return os.environ.get(key, default)
    
    def _prepare_audio_file(self, audio_data: Union[bytes, str, BytesIO]) -> str:
        """
        Prepare audio data for API request.
        
        Args:
            audio_data: Audio data as bytes, file path string, or BytesIO object.
            
        Returns:
            File handle for Gradio client.
            
        Raises:
            IndexTTSAPIError: If audio preparation fails.
        """
        try:
            if isinstance(audio_data, str):
                # File path - use directly with handle_file
                return handle_file(audio_data)
            elif isinstance(audio_data, (bytes, BytesIO)):
                # Need to save to temporary file for Gradio
                import tempfile
                import uuid
                
                if isinstance(audio_data, BytesIO):
                    audio_bytes = audio_data.getvalue()
                else:
                    audio_bytes = audio_data
                
                # Create temporary file
                temp_filename = f"temp_audio_{uuid.uuid4().hex}.wav"
                temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
                
                with open(temp_path, 'wb') as f:
                    f.write(audio_bytes)
                
                logger.debug(f"Created temporary audio file: {temp_path}")
                return handle_file(temp_path)
            else:
                raise ValueError(f"Unsupported audio data type: {type(audio_data)}")
            
        except Exception as e:
            raise IndexTTSAPIError(f"Failed to prepare audio file: {str(e)}")
    
    def generate_speech(
        self,
        text: str,
        speaker_audio: Union[bytes, str, BytesIO],
        **kwargs
    ) -> bytes:
        """
        Generate speech using voice cloning with IndexTTS.
        
        Args:
            text: Text to convert to speech.
            speaker_audio: Reference audio for voice cloning (bytes, file path, or BytesIO).
            **kwargs: Additional parameters (ignored for IndexTTS compatibility).
            
        Returns:
            Generated speech audio as bytes.
            
        Raises:
            IndexTTSAPIError: If the API request fails.
        """
        try:
            # Prepare reference audio
            prompt_audio = self._prepare_audio_file(speaker_audio)
            
            logger.info(f"Generating speech with IndexTTS - text length: {len(text)}")
            logger.debug(f"Using reference audio for voice cloning")
            
            # Call IndexTTS API
            result = self.client.predict(
                prompt=prompt_audio,
                text=text,
                api_name="/gen_single"
            )
            
            # Result should contain the generated audio file info
            if result and hasattr(result, 'get') and 'value' in result:
                audio_file_path = result['value']
                logger.info(f"IndexTTS generated audio file: {audio_file_path}")
                
                # Read the generated audio file
                with open(audio_file_path, 'rb') as f:
                    audio_data = f.read()
                
                logger.info(f"Successfully generated speech ({len(audio_data)} bytes)")
                return audio_data
            else:
                # Handle different result formats
                if isinstance(result, str) and os.path.exists(result):
                    # Direct file path
                    with open(result, 'rb') as f:
                        audio_data = f.read()
                    logger.info(f"Successfully generated speech ({len(audio_data)} bytes)")
                    return audio_data
                else:
                    raise IndexTTSAPIError(f"Unexpected result format from IndexTTS: {type(result)}")
                
        except Exception as e:
            if isinstance(e, IndexTTSAPIError):
                raise
            
            # Handle different types of exceptions
            error_msg = str(e)
            if 'token' in error_msg.lower():
                raise IndexTTSAPIError(f"Authentication error: {error_msg}")
            elif 'rate limit' in error_msg.lower() or 'quota' in error_msg.lower():
                raise IndexTTSAPIError(f"Rate limit exceeded: {error_msg}")
            elif 'network' in error_msg.lower() or 'connection' in error_msg.lower():
                raise IndexTTSAPIError(f"Network error: {error_msg}")
            else:
                raise IndexTTSAPIError(f"TTS generation failed: {error_msg}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the IndexTTS API is accessible and responding.
        
        Returns:
            Dictionary with health check status and details including HF metadata.
        """
        try:
            # Try to access the client info to check connectivity
            if hasattr(self.client, 'endpoints'):
                endpoints = self.client.endpoints
                health_data = {
                    'status': 'healthy',
                    'space_name': self.space_name,
                    'endpoints_available': len(endpoints) if endpoints else 0,
                    'note': 'API is accessible and responding'
                }
            else:
                health_data = {
                    'status': 'healthy',
                    'space_name': self.space_name,
                    'note': 'API client initialized successfully'
                }
            
            # Add Hugging Face metadata
            hf_metadata = self.get_space_metadata()
            health_data['huggingface_metadata'] = hf_metadata
            
            return health_data
            
        except Exception as e:
            error_msg = str(e)
            health_data = None
            
            if 'authentication' in error_msg.lower() or 'token' in error_msg.lower():
                health_data = {
                    'status': 'authentication_error',
                    'space_name': self.space_name,
                    'error': f"Authentication failed: {error_msg}"
                }
            elif 'rate limit' in error_msg.lower() or 'quota' in error_msg.lower():
                health_data = {
                    'status': 'rate_limited',
                    'space_name': self.space_name,
                    'error': f"Rate limited: {error_msg}"
                }
            else:
                health_data = {
                    'status': 'unhealthy',
                    'space_name': self.space_name,
                    'error': f"Service unavailable: {error_msg}"
                }
            
            # Try to add metadata even if health check failed
            try:
                hf_metadata = self.get_space_metadata()
                health_data['huggingface_metadata'] = hf_metadata
            except Exception:
                pass  # Don't let metadata errors mask the main health check error
            
            return health_data

    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the client configuration.
        
        Returns:
            Dictionary with configuration validation results.
        """
        issues = []
        
        if not self.space_name:
            issues.append("Missing Hugging Face space name")
        
        if Client is None:
            issues.append("gradio_client package not installed")
        
        if not self.hf_token:
            issues.append("No Hugging Face token (may limit access to private spaces)")
        
        return {
            'valid': len([i for i in issues if 'token' not in i]) == 0,  # Only count non-token issues as critical
            'space_name': self.space_name,
            'has_hf_token': bool(self.hf_token),
            'has_gradio_client': Client is not None,
            'issues': issues
        }
    
    def get_space_metadata(self) -> Dict[str, Any]:
        """
        Fetch metadata about the Hugging Face space being used.
        
        Returns:
            Dictionary containing space metadata including hardware info.
        """
        metadata = {
            'space_name': self.space_name,
            'space_url': f"https://huggingface.co/spaces/{self.space_name}",
            'metadata_available': False
        }
        
        if not self.hf_api:
            metadata['error'] = 'HfApi not available'
            return metadata
        
        try:
            # Get space information
            space_info = self.hf_api.space_info(self.space_name)

            print(f"DEBUGGING: Fetched space info for {self.space_name}: {space_info}")

            metadata.update({
                'metadata_available': True,
                'space_id': space_info.id,
                'author': space_info.author,
                'created_at': space_info.created_at.isoformat() if space_info.created_at else None,
                'last_modified': space_info.last_modified.isoformat() if space_info.last_modified else None,
                'likes': getattr(space_info, 'likes', 0),
                'downloads': getattr(space_info, 'downloads', 0),
                'sdk': getattr(space_info, 'sdk', 'unknown'),
                'runtime': {
                    'stage': getattr(space_info.runtime, 'stage', 'unknown') if hasattr(space_info, 'runtime') and space_info.runtime else 'unknown',
                    'hardware': getattr(space_info.runtime, 'hardware', 'unknown') if hasattr(space_info, 'runtime') and space_info.runtime else 'unknown'
                }
            })
            
            # Add hardware tier information if available
            if hasattr(space_info, 'runtime') and space_info.runtime:
                if hasattr(space_info.runtime, 'hardware'):
                    hardware = space_info.runtime.hardware
                    metadata['runtime']['hardware_display_name'] = hardware
                    
                    # Map hardware to user-friendly names
                    hardware_mapping = {
                        'cpu-basic': 'CPU Basic',
                        'cpu-upgrade': 'CPU Upgrade',
                        't4-small': 'T4 Small GPU',
                        't4-medium': 'T4 Medium GPU',
                        'a10g-small': 'A10G Small GPU',
                        'a10g-large': 'A10G Large GPU',
                        'a100-large': 'A100 Large GPU',
                        'zero-a10g': 'A10G GPU (Zero)',
                        'zero-a100': 'A100 GPU (Zero)',
                        'zero-h100': 'H100 GPU (Zero)'
                    }
                    metadata['runtime']['hardware_friendly'] = hardware_mapping.get(hardware, hardware)
            
            logger.info(f"Fetched metadata for IndexTTS space: {self.space_name}")
            
        except Exception as e:
            error_msg = str(e)
            metadata['error'] = error_msg
            logger.warning(f"Failed to fetch space metadata for {self.space_name}: {error_msg}")
        
        return metadata


# Convenience function for quick access
def create_indextts_client() -> IndexTTSClient:
    """Create an IndexTTS client with default configuration."""
    return IndexTTSClient()
