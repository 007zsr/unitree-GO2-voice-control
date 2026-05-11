from __future__ import annotations

from dataclasses import asdict, dataclass

from src.models import SemanticResult


@dataclass(frozen=True)
class LLMFallbackDecision:
    should_call: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class LLMFallbackDecider:
    def __init__(self, config: dict[str, object]):
        self.config = config

    def update_config(self, config: dict[str, object]) -> None:
        self.config = config

    def decide(
        self,
        text: str,
        traditional_result: SemanticResult | None,
        non_command_rejected: bool = False,
        normalization_rejected: bool = False,
    ) -> LLMFallbackDecision:
        cleaned = " ".join(str(text or "").strip().split())
        mode = str(self.config.get("mode") or "traditional").lower()
        provider = str(self.config.get("llm_provider") or "disabled").lower()
        if not cleaned:
            return LLMFallbackDecision(False, "empty_text")
        if normalization_rejected:
            return LLMFallbackDecision(False, "normalizer_rejected")
        if non_command_rejected:
            return LLMFallbackDecision(False, "non_command_rejected")
        if mode == "traditional":
            return LLMFallbackDecision(False, "traditional_mode")
        if mode not in {"llm_fallback", "llm_only_debug"}:
            return LLMFallbackDecision(False, "unsupported_semantic_engine_mode")
        if not bool(self.config.get("llm_enabled", False)):
            return LLMFallbackDecision(False, "llm_disabled")
        if provider == "disabled":
            return LLMFallbackDecision(False, "provider_disabled")
        if traditional_result is None:
            return LLMFallbackDecision(True, "rule_unmatched")
        if traditional_result.intent == "stop" and traditional_result.confidence >= 0.5:
            return LLMFallbackDecision(False, "stop_has_priority")
        if traditional_result.dangerous:
            return LLMFallbackDecision(False, "dangerous_rule_result")
        if bool(traditional_result.raw_result.get("fallback_allowed")):
            return LLMFallbackDecision(True, "fallback_allowed")
        if traditional_result.intent == "unknown_relative_move" and traditional_result.need_clarification:
            return LLMFallbackDecision(True, "unknown_relative_move")
        if not traditional_result.is_command:
            return LLMFallbackDecision(True, "rule_unmatched")
        if traditional_result.intent in {"unknown", "none"}:
            return LLMFallbackDecision(True, "unknown")
        min_confidence = float(self.config.get("llm_fallback_min_confidence", 0.60))
        if traditional_result.confidence < min_confidence:
            return LLMFallbackDecision(True, "low_confidence")
        return LLMFallbackDecision(False, "high_confidence_traditional_result")
