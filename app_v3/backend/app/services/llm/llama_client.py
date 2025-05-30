"""
Llama-3.1 LLM client for script generation using HuggingFace Inference API
"""
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import InferenceClient
from flask import current_app

logger = logging.getLogger(__name__)


@dataclass
class LlamaConfig:
    """Configuration for Llama-3.1 script generation"""
    model_name: str = "meta-llama/Llama-3.1-8B-Instruct"
    provider: str = "novita"
    timeout: int = 300  # 5 minutes
    max_tokens: int = 2000
    temperature: float = 0.7
    
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
    Client for interacting with Llama-3.1 using HuggingFace Inference API for script generation.
    
    This client provides script generation capabilities using the hosted Llama-3.1 model.
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
    
    def _get_client(self) -> InferenceClient:
        """Get or create the HuggingFace Inference client"""
        if self._client is None:
            # Try HF_API_TOKEN first (consistent with config), then HF_API_KEY as fallback
            api_key = self._get_config_value('HF_API_TOKEN') or self._get_config_value('HF_API_KEY')
            if not api_key:
                raise ValueError("HF_API_TOKEN not found in environment variables or config")
            
            logger.info(f"Initializing Llama client with model: {self.config.model_name}")
            logger.debug(f"Using provider: {self.config.provider}")
            
            try:
                self._client = InferenceClient(
                    provider=self.config.provider,
                    api_key=api_key,
                )
                logger.info(f"Successfully connected to HuggingFace Inference API")
            except Exception as e:
                logger.error(f"Failed to initialize Llama client: {e}")
                raise RuntimeError(f"Cannot connect to HuggingFace Inference API: {e}")
        
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
            logger.debug("Starting health check with test prompt")
            test_completion = client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": "Please respond with 'OK' if you can process this request."
                    }
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            test_response = test_completion.choices[0].message.content if test_completion.choices else "No response"
            
            self._last_health_check = current_time
            
            logger.info("Health check successful")
            return {
                'status': 'healthy',
                'model_name': self.config.model_name,
                'provider': self.config.provider,
                'test_response': str(test_response)[:100] + '...' if len(str(test_response)) > 100 else str(test_response),
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
            logger.debug(f"Using model: {self.config.model_name}")
            logger.debug(f"Temperature: {self.config.temperature}, Max tokens: {self.config.max_tokens}")
            
            client = self._get_client()
            
            # Generate script using Llama-3.1
            start_time = time.time()
            
            logger.debug("Starting script generation API call")
            completion = client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            generation_time = time.time() - start_time
            logger.info(f"Script generation completed in {generation_time:.2f} seconds")
            
            # Extract and format the result
            script_text = self._extract_script_from_result(completion)
            logger.debug(f"Generated script length: {len(script_text)} characters")
            
            # Analyze the generated script
            script_analysis = self._analyze_script(script_text)
            
            logger.info(f"Script analysis: {script_analysis['word_count']} words, "
                       f"{script_analysis['estimated_duration']} min estimated duration")
            
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
                    'model': self.config.model_name
                },
                'analysis': script_analysis,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Script generation failed: {e}", exc_info=True)
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
        
        logger.debug(f"Building script prompt with parameters: topic={topic}, "
                    f"audience={target_audience}, duration={duration_minutes}, style={style}")
        
        # Start with system instruction
        system_prompt = "You are a professional content writer specializing in spoken content for video presentations. "
        system_prompt += "Generate only the exact words that will be spoken by a presenter in a talking-head video. "
        system_prompt += "Do not include any titles, headers, production notes, background music suggestions, or formatting. "
        system_prompt += "Focus solely on creating natural, conversational spoken content.\n\n"
        
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
        full_prompt += "Please generate ONLY the spoken words that a presenter will say in a video. The output should be:\n"
        full_prompt += "1. Pure spoken content without any titles, headers, or section labels\n"
        full_prompt += "2. Natural, conversational language as if speaking directly to the audience\n"
        full_prompt += "3. No production notes, stage directions, or technical instructions\n"
        full_prompt += "4. No references to background music, editing, or visual elements\n"
        full_prompt += "5. Smooth, natural flow suitable for voice cloning and text-to-speech\n"
        full_prompt += "6. Content that starts speaking immediately without introductory titles\n\n"
        full_prompt += "SPOKEN CONTENT:"
        
        logger.debug(f"Built prompt with {len(requirements)} requirements, total length: {len(full_prompt)} characters")
        
        return full_prompt
    
    def _extract_script_from_result(self, completion: Any) -> str:
        """Extract the script text from the HuggingFace completion result"""
        try:
            if hasattr(completion, 'choices') and len(completion.choices) > 0:
                choice = completion.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    script_text = choice.message.content.strip()
                    logger.debug(f"Extracted script from completion: {len(script_text)} characters")
                    return script_text
                elif hasattr(choice, 'text'):
                    script_text = choice.text.strip()
                    logger.debug(f"Extracted script from choice.text: {len(script_text)} characters")
                    return script_text
            
            # Fallback to string conversion
            script_text = str(completion).strip()
            logger.warning(f"Using fallback extraction method: {len(script_text)} characters")
            return script_text
            
        except Exception as e:
            logger.error(f"Error extracting script from result: {e}")
            return str(completion).strip()
    
    def _analyze_script(self, script: str) -> Dict[str, Any]:
        """Analyze the generated script for metadata"""
        words = script.split()
        word_count = len(words)
        
        # Estimate speaking duration (average 150 words per minute)
        estimated_duration = round(word_count / 150.0, 1)
        
        # Count sentences and paragraphs
        sentences = script.count('.') + script.count('!') + script.count('?')
        paragraphs = len([p for p in script.split('\n\n') if p.strip()])
        
        analysis = {
            'word_count': word_count,
            'estimated_duration': estimated_duration,
            'sentence_count': sentences,
            'paragraph_count': paragraphs,
            'character_count': len(script)
        }
        
        logger.debug(f"Script analysis complete: {analysis}")
        
        return analysis


def create_llama_client(config: Optional[LlamaConfig] = None) -> LlamaClient:
    """Create a Llama client with default or custom configuration"""
    return LlamaClient(config)
