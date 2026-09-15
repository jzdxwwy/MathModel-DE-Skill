"""Environment-based configuration for real LLM model adapters.

No provider secrets are stored in the repository. Configuration is read from
process environment variables at runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "openai-compatible"
    base_url: str = ""
    api_key: Optional[str] = None
    model: str = ""
    timeout: float = 120.0

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            provider=os.getenv("MATHMODEL_LLM_PROVIDER", "openai-compatible"),
            base_url=os.getenv("MATHMODEL_LLM_BASE_URL", ""),
            api_key=os.getenv("MATHMODEL_LLM_API_KEY") or None,
            model=os.getenv("MATHMODEL_LLM_MODEL", ""),
            timeout=float(os.getenv("MATHMODEL_LLM_TIMEOUT", "120")),
        )

    def validate(self) -> None:
        if not self.provider:
            raise ValueError("MATHMODEL_LLM_PROVIDER must not be empty")
        if not self.base_url:
            raise ValueError("MATHMODEL_LLM_BASE_URL is required for a real LLM adapter")
        if not self.model:
            raise ValueError("MATHMODEL_LLM_MODEL is required for a real LLM adapter")
        if self.timeout <= 0:
            raise ValueError("MATHMODEL_LLM_TIMEOUT must be positive")

    def safe_dict(self) -> dict:
        """Return diagnostics without exposing the API key."""
        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "timeout": self.timeout,
            "api_key_configured": bool(self.api_key),
        }
