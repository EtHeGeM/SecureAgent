"""
Anthropic Provider for Claude Models
Supports Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku, etc.
"""

import time
import os
from typing import Optional, Dict, Any, List

try:
    from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base_provider import (
    BaseProvider,
    ProviderConfig,
    GenerationResponse,
    ProviderError,
    ProviderAuthError,
    ProviderRateLimitError
)


# Anthropic model pricing (as of Feb 2026, per 1M tokens in USD)
ANTHROPIC_PRICING = {
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-20240620": {"input": 3.0, "output": 15.0},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25}
}


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic Claude models"""
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize Anthropic provider
        
        Args:
            config: Provider configuration
        
        Raises:
            ImportError: If anthropic library not installed
            ProviderAuthError: If API key not provided
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic library not installed. "
                "Install with: pip install anthropic"
            )
        
        super().__init__(config)
        
        # Get API key from config or environment
        api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderAuthError(
                "Anthropic API key not found. "
                "Set ANTHROPIC_API_KEY environment variable or pass in config."
            )
        
        self.client = Anthropic(api_key=api_key)
        
        # Set pricing if not already set
        if config.model_name in ANTHROPIC_PRICING:
            pricing = ANTHROPIC_PRICING[config.model_name]
            if config.cost_per_1m_input_tokens == 0.0:
                config.cost_per_1m_input_tokens = pricing["input"]
            if config.cost_per_1m_output_tokens == 0.0:
                config.cost_per_1m_output_tokens = pricing["output"]
    
    def generate(self, prompt: str, **kwargs) -> GenerationResponse:
        """
        Generate text using Claude
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (max_tokens, temperature, etc.)
        
        Returns:
            GenerationResponse with generated text
        """
        start_time = time.time()
        
        # Prepare parameters
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.config.temperature)
        top_p = kwargs.get("top_p", self.config.top_p)
        system = kwargs.get("system", "You are a helpful AI assistant for a hospital appointment system.")
        
        try:
            # Call Anthropic API
            message = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                system=system,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract response
            response_text = message.content[0].text
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            
            latency_ms = (time.time() - start_time) * 1000
            cost = self.calculate_cost(input_tokens, output_tokens)
            
            response = GenerationResponse(
                text=response_text,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                provider="anthropic",
                model=self.config.model_name,
                metadata={
                    "stop_reason": message.stop_reason,
                    "message_id": message.id
                }
            )
            
            self._update_stats(response)
            return response
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle rate limiting
            if "rate_limit" in error_msg.lower():
                raise ProviderRateLimitError(f"Anthropic rate limit exceeded: {error_msg}")
            
            # Generic error
            latency_ms = (time.time() - start_time) * 1000
            return GenerationResponse(
                text="",
                latency_ms=latency_ms,
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                provider="anthropic",
                model=self.config.model_name,
                error=error_msg
            )
    
    def batch_generate(self, prompts: List[str], **kwargs) -> List[GenerationResponse]:
        """
        Generate responses for multiple prompts
        
        Note: Anthropic doesn't have native batch API, so this is sequential
        
        Args:
            prompts: List of prompts
            **kwargs: Generation parameters
        
        Returns:
            List of GenerationResponse objects
        """
        return [self.generate(prompt, **kwargs) for prompt in prompts]
    
    def is_available(self) -> bool:
        """
        Check if Anthropic provider is available
        
        Returns:
            True if API key is configured
        """
        try:
            # Try to list models (lightweight API call)
            # Note: This is a simplified check
            return ANTHROPIC_AVAILABLE and self.client is not None
        except:
            return False
    
    @staticmethod
    def get_available_models() -> List[str]:
        """
        Get list of available Anthropic models
        
        Returns:
            List of model names
        """
        return list(ANTHROPIC_PRICING.keys())
    
    @staticmethod
    def get_model_info(model_name: str) -> Dict[str, Any]:
        """
        Get information about a specific model
        
        Args:
            model_name: Model identifier
        
        Returns:
            Dictionary with model information
        """
        if model_name not in ANTHROPIC_PRICING:
            return {}
        
        pricing = ANTHROPIC_PRICING[model_name]
        
        # Model capabilities
        info = {
            "name": model_name,
            "provider": "anthropic",
            "pricing": pricing,
            "context_length": 200000,  # Claude 3 models support 200k context
            "supports_vision": "opus" in model_name or "sonnet" in model_name,
            "supports_function_calling": False,  # Claude uses tool use, not function calling
            "release_date": model_name.split("-")[-1] if "-" in model_name else "unknown"
        }
        
        return info


def create_anthropic_provider(
    model_name: str = "claude-3-5-sonnet-20241022",
    api_key: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.1
) -> AnthropicProvider:
    """
    Factory function to create Anthropic provider
    
    Args:
        model_name: Claude model to use
        api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
    
    Returns:
        Configured AnthropicProvider
    """
    pricing = ANTHROPIC_PRICING.get(model_name, {"input": 0.0, "output": 0.0})
    
    config = ProviderConfig(
        provider_name="anthropic",
        model_name=model_name,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
        cost_per_1m_input_tokens=pricing["input"],
        cost_per_1m_output_tokens=pricing["output"]
    )
    
    return AnthropicProvider(config)
