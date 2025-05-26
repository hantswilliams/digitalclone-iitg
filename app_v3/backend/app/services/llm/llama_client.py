"""
Llama-4 LLM client for script generation using Hugging Face Spaces
"""
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path

from gradio_client import Client
from flask import current_app

logger = logging.getLogger(__name__)


@dataclass
class LlamaConfig:
    """Configuration for Llama-4 script generation"""
    space_name: str = "openfree/Llama-4-Scout-17B-Research"
    timeout: int = 300  # 5 minutes
    max_tokens: int = 2000
    temperature: float = 0.7
    use_deep_research: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.timeout < 30:
            raise ValueError("Timeout must be at least 30 seconds")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.max_tokens < 100:
            raise ValueError("Max tokens must be at least 100")


class LlamaClient:
    """
    Client for interacting with Llama-4 on Hugging Face Spaces for script generation.
    
    This client provides script generation capabilities using the hosted Llama-4 model.
    """
    
    def __init__(self, config: Optional[LlamaConfig] = None):
        """
        Initialize the Llama client.
        
        Args:
            config: Configuration for the Llama client
        """
        self.config = config or LlamaConfig()
        self._client = None
        self._last_health_check = 0
        self._health_check_interval = 300  # 5 minutes
        
    def _get_config_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value from Flask app config or environment"""
        try:
            if current_app:
                return current_app.config.get(key, default)
        except RuntimeError:
            # Outside Flask app context
            import os
            return os.environ.get(key, default)
        return default
    
    def _get_client(self) -> Client:
        """Get or create the Gradio client"""
        if self._client is None:
            space_name = self._get_config_value('LLAMA_SPACE', self.config.space_name)
            logger.info(f"Initializing Llama client with space: {space_name}")
            
            try:
                self._client = Client(space_name)
                logger.info(f"Successfully connected to {space_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Llama client: {e}")
                raise RuntimeError(f"Cannot connect to Llama service: {e}")
        
        return self._client
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the Llama service is healthy and accessible.
        
        Returns:
            Dict with health status information
        """
        current_time = time.time()
        
        # Use cached result if recent
        if (current_time - self._last_health_check) < self._health_check_interval:
            return {'status': 'healthy', 'cached': True}
        
        try:
            client = self._get_client()
            
            # Test with a simple prompt
            test_result = client.predict(
                message="Hello! Please respond with 'OK' if you can process this request.",
                history=[],
                use_deep_research=False,
                api_name="/query_deepseek_streaming"
            )
            
            self._last_health_check = current_time
            
            return {
                'status': 'healthy',
                'space_name': self.config.space_name,
                'test_response': str(test_result)[:100] + '...' if len(str(test_result)) > 100 else str(test_result),
                'timestamp': current_time
            }
            
        except Exception as e:
            logger.error(f"Llama health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': current_time
            }
    
    def generate_script(
        self,
        prompt: str,
        topic: Optional[str] = None,
        target_audience: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        style: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a script based on the provided prompt and parameters.
        
        Args:
            prompt: Main prompt for script generation
            topic: Optional topic/subject matter
            target_audience: Optional target audience (e.g., "university students", "professionals")
            duration_minutes: Optional target duration in minutes
            style: Optional style (e.g., "formal", "conversational", "educational")
            additional_context: Optional additional context or requirements
            
        Returns:
            Dict containing the generated script and metadata
        """
        try:
            # Build comprehensive prompt
            full_prompt = self._build_script_prompt(
                prompt, topic, target_audience, duration_minutes, style, additional_context
            )
            
            logger.info(f"Generating script with prompt length: {len(full_prompt)} characters")
            
            client = self._get_client()
            
            # Generate script using Llama-4
            start_time = time.time()
            
            result = client.predict(
                message=full_prompt,
                history=[],
                use_deep_research=self.config.use_deep_research,
                api_name="/query_deepseek_streaming"
            )
            
            generation_time = time.time() - start_time
            
            # Extract and format the result
            script_text = self._extract_script_from_result(result)
            
            # Analyze the generated script
            script_analysis = self._analyze_script(script_text)
            
            return {
                'script': script_text,
                'metadata': {
                    'prompt': prompt,
                    'topic': topic,
                    'target_audience': target_audience,
                    'requested_duration': duration_minutes,
                    'style': style,
                    'generation_time': round(generation_time, 2),
                    'word_count': script_analysis['word_count'],
                    'estimated_duration': script_analysis['estimated_duration'],
                    'model': 'Llama-4-Scout-17B-Research'
                },
                'analysis': script_analysis,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return {
                'script': None,
                'error': str(e),
                'success': False
            }
    
    def _build_script_prompt(
        self,
        prompt: str,
        topic: Optional[str] = None,
        target_audience: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        style: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> str:
        """Build a comprehensive prompt for script generation"""
        
        # Start with system instruction
        system_prompt = "You are a professional script writer specializing in educational and presentation content. "
        system_prompt += "Generate a well-structured, engaging script that is suitable for a talking-head video presentation.\n\n"
        
        # Add specific requirements
        requirements = []
        
        if topic:
            requirements.append(f"Topic/Subject: {topic}")
        
        if target_audience:
            requirements.append(f"Target Audience: {target_audience}")
        
        if duration_minutes:
            words_needed = duration_minutes * 150  # Approximately 150 words per minute
            requirements.append(f"Target Duration: {duration_minutes} minutes (approximately {words_needed} words)")
        
        if style:
            requirements.append(f"Style: {style}")
        
        if additional_context:
            requirements.append(f"Additional Context: {additional_context}")
        
        # Build the full prompt
        full_prompt = system_prompt
        
        if requirements:
            full_prompt += "REQUIREMENTS:\n"
            full_prompt += "\n".join(f"- {req}" for req in requirements)
            full_prompt += "\n\n"
        
        full_prompt += "PROMPT:\n"
        full_prompt += prompt
        full_prompt += "\n\n"
        full_prompt += "Please generate a complete script that:\n"
        full_prompt += "1. Has a clear introduction, main content, and conclusion\n"
        full_prompt += "2. Is engaging and appropriate for video presentation\n"
        full_prompt += "3. Uses natural, conversational language suitable for speaking\n"
        full_prompt += "4. Includes smooth transitions between topics\n"
        full_prompt += "5. Is formatted clearly with paragraphs or sections\n\n"
        full_prompt += "SCRIPT:"
        
        return full_prompt
    
    def _extract_script_from_result(self, result: Any) -> str:
        """Extract the script text from the Llama result"""
        if isinstance(result, str):
            return result.strip()
        elif isinstance(result, (list, tuple)) and len(result) > 0:
            return str(result[0]).strip()
        elif hasattr(result, 'text'):
            return result.text.strip()
        else:
            return str(result).strip()
    
    def _analyze_script(self, script: str) -> Dict[str, Any]:
        """Analyze the generated script for metadata"""
        words = script.split()
        word_count = len(words)
        
        # Estimate speaking duration (average 150 words per minute)
        estimated_duration = round(word_count / 150.0, 1)
        
        # Count sentences and paragraphs
        sentences = script.count('.') + script.count('!') + script.count('?')
        paragraphs = len([p for p in script.split('\n\n') if p.strip()])
        
        return {
            'word_count': word_count,
            'estimated_duration': estimated_duration,
            'sentence_count': sentences,
            'paragraph_count': paragraphs,
            'character_count': len(script)
        }


def create_llama_client(config: Optional[LlamaConfig] = None) -> LlamaClient:
    """Create a Llama client with default or custom configuration"""
    return LlamaClient(config)
