import os
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
from src.core.state import state_manager
from src.config import LLM_BASE_URL, LLM_ENGINE

class LLMClient:
    """
    Standardized wrapper for LLM provider access.
    Currently defaults to OpenAI compatible APIs (allowing local Ollama use).
    """
    def __init__(self, provider: Optional[str] = None, model: str = "gpt-3.5-turbo", base_url: Optional[str] = None):
        self.provider = provider or LLM_ENGINE
        self.model = model
        
        # Load API keys internally
        self.api_key = os.environ.get("OPENAI_API_KEY") or "EMPTY_KEY"
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL") or LLM_BASE_URL
        
        if self.provider in ["openai", "ollama"]:
             # We use the openai client for both OpenAI, and local Ollama if base_url is set.
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def generate_async(self, messages: List[Dict[str, str]], timeout: int = 60) -> Optional[str]:
        """Async version of generate."""
        if state_manager.is_halted(): return None
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                timeout=timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LLMClient] Async generation failed: {e}")
            return None

    async def get_embeddings(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """Generates embeddings for the given text."""
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[LLMClient] Embedding failed: {e}")
            return [0.0] * 1536 # Fallback zero vector
