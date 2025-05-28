"""
Zyphra TTS API client for voice cloning and text-to-speech generation.

This module provides a client for the Zyphra TTS API using the official Zyphra package.
Supports voice cloning from reference audio samples and text-to-speech generation.
"""

import os
import base64
import logging
from typing import Optional, Dict, Any, Union
from io import BytesIO
from flask import current_app

try:
    from zyphra import Zyphra
except ImportError:
    Zyphra = None

logger = logging.getLogger(__name__)


class ZyphraAPIError(Exception):
    """Custom exception for Zyphra API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class ZyphraClient:
    """
    Client for Zyphra TTS API integration using the official Zyphra package.
    
    Handles voice cloning and text-to-speech generation using the Zyphra API.
    Supports base64 audio encoding and WebM output format.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Zyphra client.
        
        Args:
            api_key: Zyphra API key. If not provided, reads from config.
        """
        if Zyphra is None:
            raise ImportError("Zyphra package is required. Install with: pip install zyphra")
        
        self.api_key = api_key or self._get_config_value('ZYPHRA_API_KEY')
        
        if not self.api_key:
            raise ValueError("Zyphra API key is required. Set ZYPHRA_API_KEY environment variable.")
        
        # Initialize the official Zyphra client
        self.client = Zyphra(api_key=self.api_key)
        
        logger.info(f"Initialized Zyphra client with official package")
    
    def _get_config_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value from Flask config or environment."""
        try:
            # Try to get from Flask config first
            return getattr(current_app.config, key, None) or os.environ.get(key, default)
        except RuntimeError:
            # Not in Flask context, use environment variable
            return os.environ.get(key, default)
    
    def _encode_audio_to_base64(self, audio_data: Union[bytes, str, BytesIO]) -> str:
        """
        Encode audio data to base64 string for API request.
        
        Args:
            audio_data: Audio data as bytes, file path string, or BytesIO object.
            
        Returns:
            Base64 encoded audio string.
            
        Raises:
            ZyphraAPIError: If audio encoding fails.
        """
        try:
            if isinstance(audio_data, str):
                # File path
                with open(audio_data, 'rb') as f:
                    audio_bytes = f.read()
            elif isinstance(audio_data, BytesIO):
                # BytesIO object
                audio_bytes = audio_data.getvalue()
            elif isinstance(audio_data, bytes):
                # Raw bytes
                audio_bytes = audio_data
            else:
                raise ValueError(f"Unsupported audio data type: {type(audio_data)}")
            
            encoded = base64.b64encode(audio_bytes).decode('utf-8')
            logger.debug(f"Encoded audio data to base64 ({len(encoded)} characters)")
            return encoded
            
        except Exception as e:
            raise ZyphraAPIError(f"Failed to encode audio to base64: {str(e)}")
    
    def generate_speech(
        self,
        text: str,
        speaker_audio: Union[bytes, str, BytesIO],
        speaking_rate: float = 15.0,
        timeout: int = 60
    ) -> bytes:
        """
        Generate speech using voice cloning with the official Zyphra client.
        
        Args:
            text: Text to convert to speech.
            speaker_audio: Reference audio for voice cloning (bytes, file path, or BytesIO).
            speaking_rate: Speaking rate (default: 15.0).
            timeout: Request timeout in seconds (ignored for official client).
            
        Returns:
            Generated speech audio as bytes (WebM format).
            
        Raises:
            ZyphraAPIError: If the API request fails.
        """
        try:
            # Encode reference audio to base64
            speaker_audio_b64 = self._encode_audio_to_base64(speaker_audio)
            
            logger.info(f"Generating speech with Zyphra API - text length: {len(text)}, speaking_rate: {speaking_rate}")
            logger.debug(f"Speaker audio encoded to {len(speaker_audio_b64)} characters")
            
            # Use the official Zyphra client to generate speech
            audio_data = self.client.audio.speech.create(
                text=text,
                speaker_audio=speaker_audio_b64,
                speaking_rate=speaking_rate
            )
            
            # The official client should return bytes directly
            if isinstance(audio_data, bytes):
                logger.info(f"Successfully generated speech ({len(audio_data)} bytes)")
                return audio_data
            else:
                # If it returns something else, try to convert it
                logger.warning(f"Unexpected audio data type: {type(audio_data)}")
                if hasattr(audio_data, 'content'):
                    return audio_data.content
                elif hasattr(audio_data, 'data'):
                    return audio_data.data
                else:
                    raise ZyphraAPIError(f"Unexpected audio data format: {type(audio_data)}")
                
        except Exception as e:
            if isinstance(e, ZyphraAPIError):
                raise
            
            # Handle different types of exceptions from the official client
            error_msg = str(e)
            if 'API key' in error_msg.lower():
                raise ZyphraAPIError(f"Authentication error: {error_msg}")
            elif 'rate limit' in error_msg.lower():
                raise ZyphraAPIError(f"Rate limit exceeded: {error_msg}")
            elif 'network' in error_msg.lower() or 'connection' in error_msg.lower():
                raise ZyphraAPIError(f"Network error: {error_msg}")
            else:
                raise ZyphraAPIError(f"TTS generation failed: {error_msg}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the Zyphra API is accessible and responding.
        
        Returns:
            Dictionary with health check status and details.
        """
        try:
            # Try a simple API call to check connectivity
            # We'll use a minimal text to avoid consuming too many credits
            test_audio_b64 = base64.b64encode(b"test").decode('utf-8')
            
            # This might fail but will tell us if the API is reachable
            self.client.audio.speech.create(
                text="test",
                speaker_audio=test_audio_b64,
                speaking_rate=15.0
            )
            
            return {
                'status': 'healthy',
                'note': 'API is accessible and responding'
            }
            
        except Exception as e:
            error_msg = str(e)
            if 'authentication' in error_msg.lower() or 'api key' in error_msg.lower():
                return {
                    'status': 'authentication_error',
                    'error': f"Authentication failed: {error_msg}"
                }
            elif 'rate limit' in error_msg.lower():
                return {
                    'status': 'rate_limited',
                    'error': f"Rate limit exceeded: {error_msg}"
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f"API error: {error_msg}"
                }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the client configuration.
        
        Returns:
            Dictionary with configuration validation results.
        """
        issues = []
        
        if not self.api_key:
            issues.append("Missing API key")
        elif len(self.api_key) < 10:
            issues.append("API key appears to be too short")
        
        if Zyphra is None:
            issues.append("Zyphra package not installed")
        
        return {
            'valid': len(issues) == 0,
            'has_api_key': bool(self.api_key),
            'has_zyphra_package': Zyphra is not None,
            'issues': issues
        }


# Convenience function for quick access
def create_zyphra_client() -> ZyphraClient:
    """Create a Zyphra client with default configuration."""
    return ZyphraClient()
