"""
Audio service for text-to-speech processing and voice cloning
"""
import os
import requests
import json
import io
import datetime
from flask import current_app


class AudioService:
    """
    Service for generating audio from text using different TTS providers
    Following the "LEGO Approach" to make components swappable
    """
    
    def __init__(self):
        """
        Initialize the audio service with available TTS providers
        """
        self.providers = {
            'playht': self._playht_generate,
            # Add other providers as they become available
            # 'bark': self._bark_generate,
            # 'xtts': self._xtts_generate,
        }
        
        # Available voices in PlayHT
        self.playht_voices = {
            "male_matt": "s3://voice-cloning-zero-shot/09b5c0cc-a8f4-4450-aaab-3657b9965d0b/podcaster/manifest.json",
            "female_nichole": "s3://voice-cloning-zero-shot/7c38b588-14e8-42b9-bacd-e03d1d673c3c/nicole/manifest.json"
        }
    
    def generate_audio(self, text, voice, provider='playht'):
        """
        Generate audio from text using the specified provider
        
        Args:
            text (str): Text to convert to speech
            voice (str): Voice identifier to use
            provider (str): TTS provider to use (default: playht)
            
        Returns:
            dict: Result containing status and audio URL
        """
        if provider not in self.providers:
            return {
                'success': False,
                'error': f'Provider {provider} not supported',
                'supported_providers': list(self.providers.keys())
            }
        
        return self.providers[provider](text, voice)
    
    def _playht_generate(self, text, voice):
        """
        Generate audio using PlayHT API
        
        Args:
            text (str): Text to convert to speech
            voice (str): Voice identifier from playht_voices
            
        Returns:
            dict: Result containing status and audio URL
        """
        # Get API credentials
        userid = current_app.config['PLAYHT_USERID']
        apikey = current_app.config['PLAYHT_SECRET']
        
        if not userid or not apikey:
            current_app.logger.error("PlayHT credentials not configured")
            return {
                'success': False,
                'error': 'PlayHT credentials not configured'
            }
        
        if voice not in self.playht_voices:
            return {
                'success': False,
                'error': f'Voice {voice} not found',
                'available_voices': list(self.playht_voices.keys())
            }
        
        # Prepare API request
        url = "https://api.play.ht/api/v2/tts"
        payload = {
            "text": text,
            "voice": self.playht_voices[voice],
            "output_format": "wav",
            "voice_engine": "PlayHT2.0"
        }
        headers = {
            "accept": "text/event-stream",
            "content-type": "application/json",
            "Authorization": f"Bearer {apikey}",
            "X-USER-ID": userid
        }
        
        try:
            # Make API request
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                current_app.logger.error(f"PlayHT API error: {response.text}")
                return {
                    'success': False,
                    'error': f'PlayHT API error: {response.status_code}',
                    'details': response.text
                }
            
            # Parse the streaming response
            parsed_data = {}
            lines = response.text.split("\n")
            
            for line in lines:
                if line.startswith("data:"):
                    try:
                        # Extract the JSON data part
                        json_data = line[5:].strip()
                        if json_data:
                            data = json.loads(json_data)
                            if 'stage' in data:
                                parsed_data[data['stage']] = data
                    except json.JSONDecodeError:
                        continue
            
            if 'complete' in parsed_data:
                return {
                    'success': True,
                    'url': parsed_data['complete']['url'],
                    'voice': voice,
                    'text': text
                }
            else:
                return {
                    'success': False,
                    'error': 'Audio generation did not complete',
                    'response_data': parsed_data
                }
                
        except Exception as e:
            current_app.logger.error(f"Error generating audio with PlayHT: {str(e)}")
            return {
                'success': False,
                'error': f'PlayHT API exception: {str(e)}'
            }
