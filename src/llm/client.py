import os
from openai import OpenAI
from typing import List, Dict, Any, Optional
from src.core.state import state_manager

class LLMClient:
    """
    Standardized wrapper for LLM provider access.
    Currently defaults to OpenAI compatible APIs (allowing local Ollama use).
    """
    def __init__(self, provider: str = "openai", model: str = "gpt-3.5-turbo"):
        self.provider = provider
        self.model = model
        
        # Load API keys internally
        self.api_key = os.environ.get("OPENAI_API_KEY") or "EMPTY_KEY"
        self.base_url = os.environ.get("OPENAI_BASE_URL")
        
        if self.provider == "openai" or self.provider == "ollama":
             # We use the openai client for both OpenAI, and local Ollama if base_url is set.
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate(self, messages: List[Dict[str, str]], timeout: int = 30) -> Optional[str]:
        """
        Calls the LLM with a strict timeout. Checks global kill switch before call.
        """
        if state_manager.is_halted():
             print("[LLMClient] System halted. Aborting LLM call.")
             return None
             
        try:
            # Note: We simulate a timeout capability if the library doesn't expose it directly
            # For this MVP, we rely on the provider's default timeout or passing it to the client config
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                timeout=timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LLMClient] Generation failed: {e}")
            return None
