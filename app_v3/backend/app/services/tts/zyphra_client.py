"""
Zyphra TTS API client for voice cloning and text-to-speech generation.

This module provides a client for the Zyphra TTS API, supporting:
- Voice cloning from reference audio samples
- Text-to-speech generation with cloned voices
- WebM audio output format
- Base64 audio encoding for API requests
"""

import os
import base64
import logging
import requests
from typing import Optional, Dict, Any, Union
from io import BytesIO
from flask import current_app

logger = logging.getLogger(__name__)


class ZyphraAPIError(Exception):
    """Custom exception for Zyphra API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class ZyphraClient:
    """
    Client for Zyphra TTS API integration.
    
    Handles voice cloning and text-to-speech generation using the Zyphra API.
    Supports base64 audio encoding and WebM output format.
    """
    
    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """
        Initialize the Zyphra client.
        
        Args:
            api_key: Zyphra API key. If not provided, reads from config.
            api_url: Zyphra API base URL. If not provided, reads from config.
        """
        self.api_key = api_key or self._get_config_value('ZYPHRA_API_KEY')
        self.api_url = api_url or self._get_config_value('ZYPHRA_API_URL', 'https://api.zyphra.com/v1')
        
        if not self.api_key:
            raise ValueError("Zyphra API key is required. Set ZYPHRA_API_KEY environment variable.")
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        })
        
        logger.info(f"Initialized Zyphra client with API URL: {self.api_url}")
    
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
        Generate speech using voice cloning.
        
        Args:
            text: Text to convert to speech.
            speaker_audio: Reference audio for voice cloning (bytes, file path, or BytesIO).
            speaking_rate: Speaking rate (default: 15.0).
            timeout: Request timeout in seconds.
            
        Returns:
            Generated speech audio as bytes (WebM format).
            
        Raises:
            ZyphraAPIError: If the API request fails.
        """
        try:
            # Encode reference audio to base64
            speaker_audio_b64 = self._encode_audio_to_base64(speaker_audio)
            
            # Prepare API request payload
            payload = {
                'text': text,
                'speaking_rate': speaking_rate,
                'speaker_audio': speaker_audio_b64
            }
            
            # Make API request
            url = f"{self.api_url}/audio/text-to-speech"
            logger.info(f"Making TTS request to {url}")
            logger.debug(f"Request payload: text length={len(text)}, speaking_rate={speaking_rate}")
            
            response = self.session.post(url, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                audio_data = response.content
                logger.info(f"Successfully generated speech ({len(audio_data)} bytes)")
                return audio_data
            else:
                # Try to parse error response
                try:
                    error_data = response.json()
                except:
                    error_data = {'error': response.text}
                
                raise ZyphraAPIError(
                    f"TTS generation failed: {error_data.get('error', 'Unknown error')}",
                    status_code=response.status_code,
                    response_data=error_data
                )
                
        except requests.exceptions.Timeout:
            raise ZyphraAPIError(f"Request timed out after {timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise ZyphraAPIError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, ZyphraAPIError):
                raise
            raise ZyphraAPIError(f"Unexpected error during TTS generation: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the Zyphra API is accessible and responding.
        
        Returns:
            Dictionary with health check status and details.
        """
        try:
            # Try a minimal request to check API availability
            # Note: This assumes there's a health endpoint, otherwise we'll use a minimal TTS request
            url = f"{self.api_url}/health"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'api_url': self.api_url,
                    'response_time_ms': response.elapsed.total_seconds() * 1000
                }
            else:
                return {
                    'status': 'unhealthy',
                    'api_url': self.api_url,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'unhealthy',
                'api_url': self.api_url,
                'error': f"Connection error: {str(e)}"
            }
        except Exception as e:
            return {
                'status': 'error',
                'api_url': self.api_url,
                'error': f"Unexpected error: {str(e)}"
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
        
        if not self.api_url:
            issues.append("Missing API URL")
        elif not self.api_url.startswith(('http://', 'https://')):
            issues.append("API URL must start with http:// or https://")
        
        return {
            'valid': len(issues) == 0,
            'api_url': self.api_url,
            'has_api_key': bool(self.api_key),
            'issues': issues
        }


# Convenience function for quick access
def create_zyphra_client() -> ZyphraClient:
    """Create a Zyphra client with default configuration."""
    return ZyphraClient()
