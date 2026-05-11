from __future__ import annotations

from pathlib import Path
from typing import Any

from src.nlu.llm_provider_base import DisabledLLMProvider, LLMProvider, ReservedAPIProvider
from src.nlu.local_qwen_provider import LocalQwenProvider
from src.nlu.mock_llm_provider import MockLLMProvider


def build_llm_provider(config: dict[str, Any], root: Path | None = None) -> LLMProvider:
    provider = str(config.get("llm_provider") or "disabled").lower()
    if provider == "local_qwen":
        return LocalQwenProvider(config, root)
    if provider in {"mock", "mock_llm"}:
        return MockLLMProvider()
    if provider in {"openai_api_reserved", "custom_api_reserved"}:
        return ReservedAPIProvider(provider)
    return DisabledLLMProvider()
