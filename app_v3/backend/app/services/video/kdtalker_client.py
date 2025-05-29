"""
KDTalker client for portrait-to-video generation.

This client interfaces with KDTalker's remote Gradio service on Hugging Face Spaces
to generate talking-head videos from portrait images and audio files.
"""
import os
import time
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

try:
    from gradio_client import Client, handle_file
    GRADIO_CLIENT_AVAILABLE = True
except ImportError:
    GRADIO_CLIENT_AVAILABLE = False
    
logger = logging.getLogger(__name__)


@dataclass
class VideoGenerationConfig:
    """Configuration for video generation parameters."""
    # KDTalker specific settings - based on working debug script
    driven_audio_type: str = "upload"  # "upload" or "tts"
    smoothed_pitch: float = 0.8
    smoothed_yaw: float = 0.8
    smoothed_roll: float = 0.8
    smoothed_t: float = 0.8


class KDTalkerClient:
    """
    Client for interfacing with KDTalker via Gradio Client on Hugging Face Spaces.
    
    KDTalker is a portrait-to-video generation system that creates talking-head videos
    from portrait images and audio files with high-quality lip synchronization.
    """
    
    def __init__(
        self,
        space_name: Optional[str] = None,
        timeout: int = 300
    ):
        """
        Initialize KDTalker client.
        
        Args:
            space_name: Hugging Face Space name (defaults to env var KDTALKER_SPACE or "fffiloni/KDTalker")
            timeout: Request timeout in seconds (default: 5 minutes for video generation)
        """
        if not GRADIO_CLIENT_AVAILABLE:
            raise ImportError(
                "gradio_client is required for KDTalker integration. "
                "Install it with: pip install gradio_client"
            )
        
        self.space_name = space_name or os.getenv('KDTALKER_SPACE', 'hants/KDTalker')
        self.timeout = timeout
        self.client = None
        self.hf_token = os.getenv('HF_API_TOKEN')
        
        if not self.hf_token:
            logger.warning("HF_API_TOKEN not found in environment variables")
        
        logger.info(f"Initialized KDTalker client for space: {self.space_name}")
    
    def _get_client(self) -> Client:
        """Get or create Gradio client instance."""
        if self.client is None:
            try:
                if self.hf_token:
                    self.client = Client(self.space_name, hf_token=self.hf_token)
                else:
                    self.client = Client(self.space_name)
                logger.info(f"Connected to KDTalker space: {self.space_name}")
            except Exception as e:
                raise ConnectionError(f"Failed to connect to KDTalker space {self.space_name}: {e}")
        
        return self.client
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if KDTalker service is available and responsive.
        
        Returns:
            Dict containing health status and service information
        """
        try:
            client = self._get_client()
            
            # Test basic connectivity by trying to get space info
            # This will raise an exception if the space is not accessible
            start_time = time.time()
            _ = client.view_api()  # This checks if the space is accessible
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'service': 'kdtalker',
                'space': self.space_name,
                'response_time_ms': response_time * 1000,
                'gradio_client': True
            }
                
        except Exception as e:
            return {
                'status': 'error',
                'service': 'kdtalker',
                'error': str(e),
                'space': self.space_name,
                'gradio_client': True
            }
    
    def generate_video(
        self,
        portrait_path: Union[str, Path],
        audio_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        config: Optional[VideoGenerationConfig] = None
    ) -> Dict[str, Any]:
        """
        Generate talking-head video from portrait image and audio.
        
        Args:
            portrait_path: Path to portrait image file (PNG, JPG, JPEG)
            audio_path: Path to audio file (WAV, MP3, MP4, etc.)
            output_path: Optional output path for generated video (auto-generated if None)
            config: Video generation configuration (uses defaults if None)
            
        Returns:
            Dict containing generation results and metadata
            
        Raises:
            FileNotFoundError: If input files don't exist
            ConnectionError: If can't connect to KDTalker space
            ValueError: If generation fails or returns invalid response
        """
        if config is None:
            config = VideoGenerationConfig()
        
        portrait_path = Path(portrait_path)
        audio_path = Path(audio_path)
        
        # Validate input files
        if not portrait_path.exists():
            raise FileNotFoundError(f"Portrait image not found: {portrait_path}")
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Starting video generation with portrait: {portrait_path}, audio: {audio_path}")
        
        try:
            client = self._get_client()
            
            # Use gradio_client to call KDTalker with correct parameters
            # Based on the working debug script
            logger.info("Calling KDTalker via Gradio client...")
            start_time = time.time()
            
            result = client.predict(
                upload_driven_audio=handle_file(str(audio_path)),
                tts_driven_audio=None,  # Set to None since we're using upload audio
                driven_audio_type=config.driven_audio_type,
                source_image=handle_file(str(portrait_path)),
                smoothed_pitch=config.smoothed_pitch,
                smoothed_yaw=config.smoothed_yaw,
                smoothed_roll=config.smoothed_roll,
                smoothed_t=config.smoothed_t,
                api_name="/generate"
            )
            
            generation_time = time.time() - start_time
            logger.info(f"Video generation completed in {generation_time:.2f} seconds")
            
            # Handle the result - KDTalker returns a dict with 'video' key
            if isinstance(result, dict) and 'video' in result and result['video']:
                video_path_from_result = result['video']
            elif isinstance(result, str):
                video_path_from_result = result
            elif isinstance(result, (list, tuple)) and len(result) > 0:
                video_path_from_result = result[0]
            else:
                raise ValueError(f"Unexpected result format from KDTalker: {result}")
            
            # If output_path is specified, copy the video to the desired location
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy the video file
                import shutil
                shutil.copy2(video_path_from_result, output_path)
                final_path = str(output_path)
                file_size = output_path.stat().st_size
            else:
                final_path = video_path_from_result
                file_size = Path(final_path).stat().st_size if Path(final_path).exists() else 0
            
            # Generate metadata
            result_data = {
                'status': 'success',
                'video_path': final_path,
                'original_result': video_path_from_result,
                'file_size': file_size,
                'generation_time': generation_time,
                'config': {
                    'driven_audio_type': config.driven_audio_type,
                    'smoothed_pitch': config.smoothed_pitch,
                    'smoothed_yaw': config.smoothed_yaw,
                    'smoothed_roll': config.smoothed_roll,
                    'smoothed_t': config.smoothed_t
                },
                'input_files': {
                    'portrait': str(portrait_path),
                    'audio': str(audio_path)
                },
                'space': self.space_name,
                'timestamp': time.time()
            }
            
            logger.info(f"Video generation successful: {final_path} ({file_size} bytes)")
            return result_data
            
        except Exception as e:
            error_msg = f"Video generation failed: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate client configuration and connectivity.
        
        Returns:
            Dict containing validation results
        """
        validation_result = {
            'client_config': True,
            'space_name': self.space_name,
            'timeout': self.timeout,
            'gradio_client_available': GRADIO_CLIENT_AVAILABLE
        }
        
        if not GRADIO_CLIENT_AVAILABLE:
            validation_result.update({
                'connectivity': False,
                'error': 'gradio_client not available'
            })
            return validation_result
        
        # Test connectivity
        health_result = self.health_check()
        validation_result.update({
            'connectivity': health_result['status'] == 'healthy',
            'health_check': health_result
        })
        
        return validation_result


# Convenience function for quick video generation
def generate_talking_head(
    portrait_path: Union[str, Path],
    audio_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for generating talking-head videos.
    
    Args:
        portrait_path: Path to portrait image
        audio_path: Path to audio file
        output_path: Optional output path
        **kwargs: Additional configuration parameters
        
    Returns:
        Dict containing generation results
    """
    config = VideoGenerationConfig(**kwargs)
    client = KDTalkerClient()
    return client.generate_video(portrait_path, audio_path, output_path, config)


# Convenience function for quick video generation
def generate_talking_head(
    portrait_path: Union[str, Path],
    audio_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for generating talking-head videos.
    
    Args:
        portrait_path: Path to portrait image
        audio_path: Path to audio file
        output_path: Optional output path
        **kwargs: Additional configuration parameters
        
    Returns:
        Dict containing generation results
    """
    config = VideoGenerationConfig(**kwargs)
    client = KDTalkerClient()
    return client.generate_video(portrait_path, audio_path, output_path, config)
