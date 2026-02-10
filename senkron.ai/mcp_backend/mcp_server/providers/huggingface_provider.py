"""
HuggingFace Provider for Local Models
Supports Llama, Qwen, Mistral, Gemma, and other open-source models
"""

import time
from typing import Optional, Dict, Any, List
import torch

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .base_provider import (
    BaseProvider,
    ProviderConfig,
    GenerationResponse,
    ProviderError
)


class HuggingFaceProvider(BaseProvider):
    """Provider for local HuggingFace models"""
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize HuggingFace provider
        
        Args:
            config: Provider configuration with extra_params:
                - quantization: "int4", "int8", or "fp16"
                - device_map: "auto", "cuda", or "cpu"
                - trust_remote_code: bool
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "Transformers library not installed. "
                "Install with: pip install transformers accelerate bitsandbytes"
            )
        
        super().__init__(config)
        
        # Get configuration
        self.quantization = config.extra_params.get("quantization", "int4")
        self.device_map = config.extra_params.get("device_map", "auto")
        self.trust_remote_code = config.extra_params.get("trust_remote_code", True)
        
        # Load model and tokenizer
        print(f"Loading {config.model_name} with {self.quantization} quantization...")
        self.tokenizer, self.model = self._load_model()
        print("✅ Model loaded successfully!")
    
    def _load_model(self):
        """Load model with specified quantization"""
        tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name,
            trust_remote_code=self.trust_remote_code
        )
        
        if self.quantization == "int4":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16
            )
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                quantization_config=bnb_config,
                device_map=self.device_map,
                trust_remote_code=self.trust_remote_code
            )
        elif self.quantization == "int8":
            bnb_config = BitsAndBytesConfig(load_in_8bit=True)
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                quantization_config=bnb_config,
                device_map=self.device_map,
                trust_remote_code=self.trust_remote_code
            )
        else:  # fp16 or default
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                torch_dtype=torch.float16,
                device_map=self.device_map,
                trust_remote_code=self.trust_remote_code
            )
        
        return tokenizer, model
    
    def generate(self, prompt: str, **kwargs) -> GenerationResponse:
        """
        Generate text using local model
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
        
        Returns:
            GenerationResponse
        """
        start_time = time.time()
        
        # Prepare parameters
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        temperature = kwargs.get("temperature", self.config.temperature)
        top_p = kwargs.get("top_p", self.config.top_p)
        system = kwargs.get("system", "You are a helpful AI assistant for a hospital appointment system.")
        
        try:
            # Format messages
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
            
            # Apply chat template
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Tokenize
            inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            input_length = inputs.input_ids.shape[1]
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=(temperature > 0.0)
                )
            
            # Decode
            generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the assistant's response
            if "<|im_start|>assistant" in generated:
                response_text = generated.split("<|im_start|>assistant")[-1].strip()
            elif "assistant\n" in generated:
                response_text = generated.split("assistant\n")[-1].strip()
            else:
                # Fallback: remove the input prompt
                response_text = generated[len(text):].strip()
            
            # Calculate tokens
            output_length = outputs.shape[1]
            input_tokens = input_length
            output_tokens = output_length - input_length
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Local models have no API cost
            cost = 0.0
            
            response = GenerationResponse(
                text=response_text,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                provider="local",
                model=self.config.model_name,
                metadata={
                    "quantization": self.quantization,
                    "device": str(self.model.device)
                }
            )
            
            self._update_stats(response)
            return response
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return GenerationResponse(
                text="",
                latency_ms=latency_ms,
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                provider="local",
                model=self.config.model_name,
                error=str(e),
                metadata={"quantization": self.quantization}
            )
    
    def batch_generate(self, prompts: List[str], **kwargs) -> List[GenerationResponse]:
        """
        Generate responses for multiple prompts
        
        Currently sequential, could be optimized with batching
        
        Args:
            prompts: List of prompts
            **kwargs: Generation parameters
        
        Returns:
            List of GenerationResponse objects
        """
        return [self.generate(prompt, **kwargs) for prompt in prompts]
    
    def is_available(self) -> bool:
        """
        Check if model is loaded and available
        
        Returns:
            True if model is loaded
        """
        return self.model is not None and self.tokenizer is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about loaded model
        
        Returns:
            Dictionary with model information
        """
        try:
            # Get model size (approximate via parameters)
            param_count = sum(p.numel() for p in self.model.parameters())
            param_size_gb = (param_count * 2) / (1024**3)  # Approximate for fp16
            
            if self.quantization == "int4":
                param_size_gb /= 4
            elif self.quantization == "int8":
                param_size_gb /= 2
            
            return {
                "model_name": self.config.model_name,
                "quantization": self.quantization,
                "parameters": param_count,
                "approx_size_gb": round(param_size_gb, 2),
                "device": str(self.model.device),
                "dtype": str(self.model.dtype)
            }
        except:
            return {"model_name": self.config.model_name}


def create_huggingface_provider(
    model_name: str,
    quantization: str = "int4",
    max_tokens: int = 512,
    temperature: float = 0.1
) -> HuggingFaceProvider:
    """
    Factory function to create HuggingFace provider
    
    Args:
        model_name: HuggingFace model identifier
        quantization: "int4", "int8", or "fp16"
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
    
    Returns:
        Configured HuggingFaceProvider
    """
    config = ProviderConfig(
        provider_name="local",
        model_name=model_name,
        max_tokens=max_tokens,
        temperature=temperature,
        cost_per_1m_input_tokens=0.0,  # Local models are free (ignoring infra costs)
        cost_per_1m_output_tokens=0.0,
        extra_params={
            "quantization": quantization,
            "device_map": "auto",
            "trust_remote_code": True
        }
    )
    
    return HuggingFaceProvider(config)
