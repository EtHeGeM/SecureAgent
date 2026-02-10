"""
Base Provider Interface for Multi-Provider LLM System
Defines abstract interface for all LLM providers (Anthropic, OpenAI, Local, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import time


class ProviderType(Enum):
    """Provider types"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class ProviderConfig:
    """Configuration for a provider"""
    provider_name: str
    model_name: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    max_tokens: int = 512
    temperature: float = 0.1
    top_p: float = 0.95
    
    # Cost tracking (per 1M tokens in USD)
    cost_per_1m_input_tokens: float = 0.0
    cost_per_1m_output_tokens: float = 0.0
    
    # Provider-specific settings
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    # Rate limiting
    max_requests_per_minute: int = 60
    max_tokens_per_minute: int = 100000


@dataclass
class GenerationResponse:
    """Response from a generation request"""
    text: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    provider: str
    model: str
    
    # Optional metadata
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used"""
        return self.input_tokens + self.output_tokens
    
    @property
    def success(self) -> bool:
        """Whether generation succeeded"""
        return self.error is None


class BaseProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize provider
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self._request_count = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost = 0.0
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> GenerationResponse:
        """
        Generate text from prompt
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
        
        Returns:
            GenerationResponse with generated text and metadata
        """
        pass
    
    def batch_generate(self, prompts: List[str], **kwargs) -> List[GenerationResponse]:
        """
        Generate responses for multiple prompts (default: sequential)
        
        Subclasses can override for true batch API support
        
        Args:
            prompts: List of input prompts
            **kwargs: Additional generation parameters
        
        Returns:
            List of GenerationResponse objects
        """
        return [self.generate(prompt, **kwargs) for prompt in prompts]
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available and configured correctly
        
        Returns:
            True if provider can be used
        """
        pass
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost in USD
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            Cost in USD
        """
        cost = (
            (input_tokens / 1_000_000) * self.config.cost_per_1m_input_tokens +
            (output_tokens / 1_000_000) * self.config.cost_per_1m_output_tokens
        )
        return round(cost, 6)
    
    def _update_stats(self, response: GenerationResponse):
        """Update internal statistics"""
        self._request_count += 1
        self._total_input_tokens += response.input_tokens
        self._total_output_tokens += response.output_tokens
        self._total_cost += response.cost_usd
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get provider usage statistics
        
        Returns:
            Dictionary with usage stats
        """
        return {
            "provider": self.config.provider_name,
            "model": self.config.model_name,
            "total_requests": self._request_count,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "total_cost_usd": round(self._total_cost, 4),
            "avg_input_tokens_per_request": (
                self._total_input_tokens / self._request_count if self._request_count > 0 else 0
            ),
            "avg_output_tokens_per_request": (
                self._total_output_tokens / self._request_count if self._request_count > 0 else 0
            ),
            "avg_cost_per_request": (
                self._total_cost / self._request_count if self._request_count > 0 else 0
            )
        }
    
    def reset_stats(self):
        """Reset usage statistics"""
        self._request_count = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost = 0.0
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.config.provider_name}, model={self.config.model_name})"


class ProviderError(Exception):
    """Base exception for provider errors"""
    pass


class ProviderAuthError(ProviderError):
    """Authentication/API key error"""
    pass


class ProviderRateLimitError(ProviderError):
    """Rate limit exceeded"""
    pass


class ProviderTimeoutError(ProviderError):
    """Request timeout"""
    pass
