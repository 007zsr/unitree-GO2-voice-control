from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Any

from src.commands.go2_action_catalog import Go2ActionCatalog
from src.models import SemanticResult
from src.nlu.keyword_candidate import detect_source_language


FORBIDDEN_TOKENS = [
    "SportClient",
    "unitree_sdk",
    "unitree_sdk2py",
    "Move(",
    "StandUp(",
    "StopMove(",
    "import ",
    "def ",
    "class ",
    "```python",
    "subprocess",
    "os.system",
]

RISK_LEVELS = {"safe", "caution", "dangerous", "disabled"}
NON_EXECUTING_INTENTS = {"unknown", "none"}
MOTION_INTENTS = {"move_forward", "move_backward", "turn_left", "turn_right"}


@dataclass(frozen=True)
class LLMSemanticCandidate:
    intent: str
    confidence: float
    risk: str
    needs_confirmation: bool
    reason: str
    provider: str
    raw_text: str
    valid: bool = True
    error_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LLMOutputParser:
    def parse_candidate(self, raw_output: str, provider: str) -> LLMSemanticCandidate:
        cleaned = self._strip_code_fence(raw_output)
        if any(token in cleaned for token in FORBIDDEN_TOKENS):
            return self._invalid(provider, raw_output, "forbidden_output_token")
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return self._invalid(provider, raw_output, "json_parse_failed")
        if not isinstance(data, dict):
            return self._invalid(provider, raw_output, "json_not_object")
        if "commands" in data and isinstance(data.get("commands"), list) and data["commands"]:
            first = data["commands"][0]
            if isinstance(first, dict):
                data = {**data, **first}
        missing = [
            key
            for key in ["intent", "confidence", "needs_confirmation", "risk", "reason"]
            if key not in data and not (key == "needs_confirmation" and "need_clarification" in data)
        ]
        if missing:
            return self._invalid(provider, raw_output, "missing_fields")
        try:
            confidence = float(data.get("confidence"))
        except (TypeError, ValueError):
            return self._invalid(provider, raw_output, "invalid_confidence")
        if confidence < 0.0 or confidence > 1.0:
            return self._invalid(provider, raw_output, "invalid_confidence")
        risk = str(data.get("risk") or data.get("risk_level") or "").lower()
        if not risk and bool(data.get("dangerous")):
            risk = "dangerous"
        if risk not in RISK_LEVELS:
            return self._invalid(provider, raw_output, "invalid_risk")
        return LLMSemanticCandidate(
            intent=str(data.get("intent") or "unknown"),
            confidence=confidence,
            needs_confirmation=bool(data.get("needs_confirmation", data.get("need_clarification", False))),
            risk=risk,
            reason=str(data.get("reason") or ""),
            provider=provider,
            raw_text=raw_output,
        )

    def to_semantic_result(
        self,
        candidate: LLMSemanticCandidate,
        input_text: str,
        allowed_intents: set[str],
        action_catalog: Go2ActionCatalog,
        fallback_reason: str,
        provider_latency_ms: float,
        provider_status: dict[str, Any] | None = None,
    ) -> SemanticResult:
        if not candidate.valid:
            return self._unknown_semantic(
                input_text,
                candidate,
                fallback_reason,
                provider_latency_ms,
                "invalid_llm_output",
                provider_status,
            )
        if candidate.intent not in allowed_intents:
            invalid = LLMSemanticCandidate(
                intent="unknown",
                confidence=0.0,
                needs_confirmation=True,
                risk="safe",
                reason=f"LLM returned intent outside allowed set: {candidate.intent}",
                provider=candidate.provider,
                raw_text=candidate.raw_text,
                valid=False,
                error_type="intent_not_allowed",
            )
            return self._unknown_semantic(
                input_text,
                invalid,
                fallback_reason,
                provider_latency_ms,
                "intent_not_allowed",
                provider_status,
            )
        if self._relative_move_without_direction(input_text, candidate.intent):
            invalid = LLMSemanticCandidate(
                intent="unknown",
                confidence=0.0,
                needs_confirmation=True,
                risk="safe",
                reason="LLM tried to infer a motion command from relative wording without direction.",
                provider=candidate.provider,
                raw_text=candidate.raw_text,
                valid=False,
                error_type="relative_move_without_direction",
            )
            return self._unknown_semantic(
                input_text,
                invalid,
                fallback_reason,
                provider_latency_ms,
                "relative_move_without_direction",
                provider_status,
            )
        if candidate.confidence < 0.50:
            return self._unknown_semantic(
                input_text,
                candidate,
                fallback_reason,
                provider_latency_ms,
                "confidence_below_unknown_threshold",
                provider_status,
            )
        if candidate.intent in NON_EXECUTING_INTENTS:
            return self._unknown_semantic(
                input_text,
                candidate,
                fallback_reason,
                provider_latency_ms,
                "llm_returned_unknown",
                provider_status,
            )

        action = action_catalog.get(candidate.intent)
        action_risk = action.risk_level if action else candidate.risk
        risk = "dangerous" if candidate.risk == "dangerous" or action_risk == "dangerous" else action_risk
        needs_confirmation = (
            candidate.needs_confirmation
            or candidate.confidence < 0.75
            or risk in {"dangerous", "disabled"}
            or bool(action and action.requires_manual_confirm)
            or bool(action and not action.voice_enabled)
        )
        executable = bool(action and action.voice_enabled and risk not in {"dangerous", "disabled"})
        return SemanticResult(
            is_command=True,
            intent=candidate.intent,
            duration_sec=None,
            speed_level="slow",
            source_language=detect_source_language(input_text),
            confidence=candidate.confidence,
            need_clarification=needs_confirmation,
            dangerous=risk == "dangerous",
            risk_level=risk,
            executable=executable,
            rejected_by_nlu=risk == "disabled",
            reason=candidate.reason or "LLM fallback semantic candidate accepted.",
            raw_output=candidate.raw_text,
            raw_result={
                **self._llm_raw_result(candidate, fallback_reason, provider_latency_ms, provider_status),
                "provider": "llm_fallback",
                "llm_provider": candidate.provider,
                "llm_output_valid": True,
                "final_semantic_source": "llm_fallback",
                "catalog_risk_level": action_risk,
                "voice_enabled": bool(action.voice_enabled) if action else False,
            },
        )

    def unavailable_result(
        self,
        input_text: str,
        provider: str,
        fallback_reason: str,
        latency_ms: float,
        error_type: str,
        error_message: str,
        provider_status: dict[str, Any] | None = None,
    ) -> SemanticResult:
        candidate = LLMSemanticCandidate(
            intent="unknown",
            confidence=0.0,
            needs_confirmation=True,
            risk="safe",
            reason=error_message,
            provider=provider,
            raw_text="",
            valid=False,
            error_type=error_type,
        )
        return self._unknown_semantic(
            input_text,
            candidate,
            fallback_reason,
            latency_ms,
            error_type,
            provider_status,
        )

    def _unknown_semantic(
        self,
        input_text: str,
        candidate: LLMSemanticCandidate,
        fallback_reason: str,
        latency_ms: float,
        error_type: str,
        provider_status: dict[str, Any] | None,
    ) -> SemanticResult:
        return SemanticResult(
            is_command=False,
            intent="unknown",
            source_language=detect_source_language(input_text),
            confidence=min(max(candidate.confidence, 0.0), 0.49),
            need_clarification=True,
            dangerous=False,
            risk_level="safe",
            executable=False,
            rejected_by_nlu=True,
            reason=candidate.reason or error_type,
            raw_output=candidate.raw_text,
            raw_result={
                **self._llm_raw_result(candidate, fallback_reason, latency_ms, provider_status),
                "provider": "llm_fallback",
                "llm_provider": candidate.provider,
                "llm_output_valid": False,
                "llm_error_type": error_type,
                "final_semantic_source": "llm_fallback",
            },
        )

    def _llm_raw_result(
        self,
        candidate: LLMSemanticCandidate,
        fallback_reason: str,
        latency_ms: float,
        provider_status: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "source": "llm_fallback",
            "fallback_triggered": True,
            "fallback_reason": fallback_reason,
            "llm_raw_output": candidate.raw_text,
            "llm_parsed_intent": candidate.intent,
            "llm_confidence": candidate.confidence,
            "llm_needs_confirmation": candidate.needs_confirmation,
            "llm_risk": candidate.risk,
            "llm_latency_ms": latency_ms,
            "llm_candidate": candidate.to_dict(),
            "llm_available": bool(provider_status or {}),
            "llm_model_status": provider_status or {},
        }

    def _invalid(self, provider: str, raw_output: str, error_type: str) -> LLMSemanticCandidate:
        return LLMSemanticCandidate(
            intent="unknown",
            confidence=0.0,
            needs_confirmation=True,
            risk="safe",
            reason=error_type,
            provider=provider,
            raw_text=raw_output,
            valid=False,
            error_type=error_type,
        )

    def _strip_code_fence(self, text: str) -> str:
        stripped = str(text or "").strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                return "\n".join(lines[1:-1]).strip()
        return stripped

    def _relative_move_without_direction(self, text: str, intent: str) -> bool:
        if intent not in MOTION_INTENTS:
            return False
        lowered = text.lower()
        has_relative_request = bool(
            re.search(r"\bcome here\b", lowered)
            or re.search(r"\bcome\s+to\s+me\b", lowered)
            or re.search(r"\bcome\s+closer\b", lowered)
            or "过来" in text
            or "靠近我" in text
        )
        has_direction = bool(
            re.search(r"\b(forward|back|backward|left|right)\b", lowered)
            or any(marker in text for marker in ["前", "后", "左", "右"])
            or re.search(r"\byour\s+(left|right)\b", lowered)
        )
        return has_relative_request and not has_direction
