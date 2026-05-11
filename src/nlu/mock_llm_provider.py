from __future__ import annotations

import json
import time
from typing import Any

from src.nlu.llm_provider_base import LLMProviderContext, LLMProviderResult


class MockLLMProvider:
    name = "mock"

    def __init__(self, outputs: dict[str, str | dict[str, Any]] | None = None, available: bool = True):
        self.outputs = outputs or {}
        self.available = available
        self.call_count = 0
        self.last_context: LLMProviderContext | None = None

    def status(self) -> dict[str, Any]:
        return {"provider": self.name, "available": self.available, "reason": "test_provider"}

    def generate(self, context: LLMProviderContext) -> LLMProviderResult:
        self.call_count += 1
        self.last_context = context
        started = time.monotonic()
        if not self.available:
            return LLMProviderResult(
                provider=self.name,
                available=False,
                error_type="provider_unavailable",
                error_message="Mock LLM provider is unavailable.",
                latency_ms=(time.monotonic() - started) * 1000,
                model_status=self.status(),
            )
        raw = self.outputs.get(context.normalized_text)
        if raw is None:
            raw = self._default_output(context.normalized_text)
        if isinstance(raw, dict):
            raw_text = json.dumps(raw, ensure_ascii=False)
        else:
            raw_text = str(raw)
        return LLMProviderResult(
            provider=self.name,
            available=True,
            raw_output=raw_text,
            latency_ms=(time.monotonic() - started) * 1000,
            model_status=self.status(),
        )

    def _default_output(self, text: str) -> dict[str, Any]:
        lowered = text.lower()
        if "take a seat" in lowered or "could you sit down" in lowered:
            return {
                "intent": "sit_down",
                "confidence": 0.86,
                "needs_confirmation": False,
                "risk": "safe",
                "reason": "Mock provider mapped a sitting request.",
            }
        if "起来" in text or "please rise" in lowered or "rise" == lowered.strip(" .!?"):
            return {
                "intent": "stand_up",
                "confidence": 0.86,
                "needs_confirmation": False,
                "risk": "safe",
                "reason": "Mock provider mapped a stand-up request.",
            }
        if "forbidden acrobatic" in lowered or "backflip" in lowered or "back flip" in lowered:
            return {
                "intent": "back_flip",
                "confidence": 0.90,
                "needs_confirmation": True,
                "risk": "dangerous",
                "reason": "Mock provider recognized a dangerous flip.",
            }
        if "front jump" in lowered:
            return {
                "intent": "front_jump",
                "confidence": 0.90,
                "needs_confirmation": True,
                "risk": "dangerous",
                "reason": "Mock provider recognized a dangerous jump.",
            }
        if "come here" in lowered or "come closer" in lowered:
            return {
                "intent": "unknown",
                "confidence": 0.35,
                "needs_confirmation": True,
                "risk": "safe",
                "reason": "Mock provider refuses to infer forward motion from relative wording.",
            }
        return {
            "intent": "unknown",
            "confidence": 0.20,
            "needs_confirmation": True,
            "risk": "safe",
            "reason": "Mock provider is uncertain.",
        }
