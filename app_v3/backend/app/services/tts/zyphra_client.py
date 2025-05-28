"""
Zyphra TTS API client for voice cloning and text-to-speech generation.

This module provides a client for the Zyphra TTS API using the Gradio client approach
to access the Hugging Face Space that provides Zyphra functionality.
Supports voice cloning from reference audio samples and text-to-speech generation.
"""

import os
import base64
import logging
import tempfile
import shutil
from typing import Optional, Dict, Any, Union
from io import BytesIO
from flask import current_app

try:
    from gradio_client import Client, handle_file
except ImportError:
    Client = None
    handle_file = None

logger = logging.getLogger(__name__)


class ZyphraAPIError(Exception):
    """Custom exception for Zyphra API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class ZyphraClient:
    """
    Client for Zyphra TTS API integration using Gradio client to access HuggingFace Space.
    
    Handles voice cloning and text-to-speech generation using the Zyphra API through
    the ginigen/VoiceClone-TTS Hugging Face Space.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Zyphra client.
        
        Args:
            api_key: Not used for Gradio client approach, kept for compatibility.
        """
        if Client is None or handle_file is None:
            raise ImportError("gradio_client package is required. Install with: pip install gradio_client")
        
        # Initialize the Gradio client
        self.gradio_client = Client("ginigen/VoiceClone-TTS")
        
        logger.info(f"Initialized Zyphra client with Gradio Space: ginigen/VoiceClone-TTS")
    
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
        Prepare audio data for Gradio client by saving it to a temporary file.
        
        Args:
            audio_data: Audio data as bytes, file path string, or BytesIO object.
            
        Returns:
            Path to temporary audio file.
            
        Raises:
            ZyphraAPIError: If audio preparation fails.
        """
        try:
            if isinstance(audio_data, str):
                # File path - return as is
                if os.path.exists(audio_data):
                    return audio_data
                else:
                    raise ValueError(f"Audio file not found: {audio_data}")
                    
            elif isinstance(audio_data, (bytes, BytesIO)):
                # Save to temporary file
                if isinstance(audio_data, BytesIO):
                    audio_bytes = audio_data.getvalue()
                else:
                    audio_bytes = audio_data
                
                # Create temporary file
                temp_fd, temp_path = tempfile.mkstemp(suffix='.wav', prefix='zyphra_audio_')
                try:
                    with os.fdopen(temp_fd, 'wb') as temp_file:
                        temp_file.write(audio_bytes)
                    return temp_path
                except:
                    os.unlink(temp_path)  # Clean up on error
                    raise
                    
            else:
                raise ValueError(f"Unsupported audio data type: {type(audio_data)}")
            
        except Exception as e:
            raise ZyphraAPIError(f"Failed to prepare audio file: {str(e)}")
    
    def generate_speech(
        self,
        text: str,
        speaker_audio: Union[bytes, str, BytesIO],
        speaking_rate: float = 15.0,
        timeout: int = 300  # Gradio can be slower, so longer timeout
    ) -> bytes:
        """
        Generate speech using voice cloning with the Gradio client.
        
        Args:
            text: Text to convert to speech.
            speaker_audio: Reference audio for voice cloning (bytes, file path, or BytesIO).
            speaking_rate: Speaking rate (default: 15.0).
            timeout: Request timeout in seconds.
            
        Returns:
            Generated speech audio as bytes (WAV format).
            
        Raises:
            ZyphraAPIError: If the API request fails.
        """
        temp_audio_path = None
        try:
            # Prepare audio file for Gradio
            temp_audio_path = self._prepare_audio_file(speaker_audio)
            
            logger.info(f"Generating speech with Zyphra via Gradio - text length: {len(text)}, speaking_rate: {speaking_rate}")
            logger.debug(f"Using voice file: {temp_audio_path}")
            
            # Use the Gradio client to generate speech
            result = self.gradio_client.predict(
                model_choice="Zyphra/Zonos-v0.1-transformer",
                text=text,
                language="en-us",  # TODO: Make this configurable
                speaker_audio=handle_file(temp_audio_path),
                prefix_audio=handle_file('https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav'),
                e1=1,          # Happiness
                e2=0.05,       # Sadness
                e3=0.05,       # Disgust
                e4=0.05,       # Fear
                e5=0.05,       # Surprise
                e6=0.05,       # Anger
                e7=0.1,        # Other
                e8=0.2,        # Neutral
                vq_single=0.78,      # Voice Clarity
                fmax=24000,          # Frequency Max (Hz)
                pitch_std=45,        # Pitch Variation
                speaking_rate=speaking_rate,    # Speaking Rate
                dnsmos_ovrl=4,       # Voice Quality
                speaker_noised=False, # Denoise Speaker
                cfg_scale=2,         # Guidance Scale
                min_p=0.15,          # Min P (Randomness)
                seed=420,            # Seed
                randomize_seed=True, # Randomize Seed
                unconditional_keys=["emotion"], # Unconditional Keys
                api_name="/generate_audio"
            )
            
            # Result should be a tuple: (generated_audio_filepath, seed)
            if result and len(result) >= 1:
                generated_audio_path = result[0]
                seed_used = result[1] if len(result) > 1 else "unknown"
                
                # Read the generated audio file
                if hasattr(generated_audio_path, 'name'):
                    actual_path = generated_audio_path.name
                else:
                    actual_path = str(generated_audio_path)
                
                if os.path.exists(actual_path):
                    with open(actual_path, 'rb') as f:
                        audio_data = f.read()
                    
                    logger.info(f"Successfully generated speech ({len(audio_data)} bytes, seed: {seed_used})")
                    return audio_data
                else:
                    raise ZyphraAPIError(f"Generated audio file not found: {actual_path}")
            else:
                raise ZyphraAPIError("No result returned from Gradio TTS generation")
                
        except Exception as e:
            if isinstance(e, ZyphraAPIError):
                raise
            
            # Handle different types of exceptions
            error_msg = str(e)
            if 'timeout' in error_msg.lower():
                raise ZyphraAPIError(f"Request timed out: {error_msg}")
            elif 'connection' in error_msg.lower() or 'network' in error_msg.lower():
                raise ZyphraAPIError(f"Network error: {error_msg}")
            else:
                raise ZyphraAPIError(f"TTS generation failed: {error_msg}")
        
        finally:
            # Clean up temporary file if we created one
            if temp_audio_path and temp_audio_path != speaker_audio and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass  # Ignore cleanup errors
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the Zyphra Gradio Space is accessible and responding.
        
        Returns:
            Dictionary with health check status and details.
        """
        try:
            # Try to get the space info to check if it's accessible
            # This is a lightweight check
            info = self.gradio_client.view_api()
            
            return {
                'status': 'healthy',
                'note': 'Gradio Space is accessible',
                'space_info': 'ginigen/VoiceClone-TTS'
            }
            
        except Exception as e:
            error_msg = str(e)
            if 'connection' in error_msg.lower() or 'network' in error_msg.lower():
                return {
                    'status': 'connection_error',
                    'error': f"Cannot connect to Gradio Space: {error_msg}"
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f"Gradio Space error: {error_msg}"
                }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the client configuration.
        
        Returns:
            Dictionary with configuration validation results.
        """
        issues = []
        
        if Client is None:
            issues.append("gradio_client package not installed")
        
        return {
            'valid': len(issues) == 0,
            'has_gradio_client': Client is not None,
            'space_url': 'ginigen/VoiceClone-TTS',
            'issues': issues
        }


# Convenience function for quick access
def create_zyphra_client() -> ZyphraClient:
    """Create a Zyphra client with default configuration."""
    return ZyphraClient()
