from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from src.models import SemanticResult


@dataclass(frozen=True)
class LLMProviderContext:
    normalized_text: str
    asr_language: str
    rule_nlu_result: SemanticResult | None
    allowed_intents: list[str]
    action_catalog_summary: list[dict[str, Any]]
    safety_policy_summary: str
    semantic_engine_mode: str

    def prompt_messages(self) -> list[dict[str, str]]:
        allowed = ", ".join(self.allowed_intents)
        catalog_lines = []
        for item in self.action_catalog_summary:
            aliases = item.get("aliases") or {}
            en = ", ".join(str(alias) for alias in aliases.get("en", [])[:4]) if isinstance(aliases, dict) else ""
            zh = ", ".join(str(alias) for alias in aliases.get("zh", [])[:4]) if isinstance(aliases, dict) else ""
            catalog_lines.append(
                f"- {item.get('intent')}: risk={item.get('risk_level')}, voice={item.get('voice_enabled')}, "
                f"aliases_en=[{en}], aliases_zh=[{zh}]"
            )
        rule_result = self.rule_nlu_result.to_dict() if self.rule_nlu_result else {}
        system = (
            "You are not a robot controller. You are only a semantic classifier for a Unitree Go2 "
            "voice-control pipeline. Choose exactly one intent from allowed_intents. Do not produce "
            "SDK calls, Python code, shell commands, or a natural-language action plan. Do not invent "
            "new intents. If uncertain, return intent=unknown. Dangerous actions must keep "
            "risk=dangerous. The real SafetyController will decide whether anything may execute."
        )
        user = (
            "Return exactly one JSON object with this schema and no extra text:\n"
            '{"intent":"sit_down","confidence":0.86,"needs_confirmation":false,'
            '"risk":"safe","reason":"short reason"}\n\n'
            f"allowed_intents: {allowed}\n"
            "action_catalog_summary:\n"
            + "\n".join(catalog_lines)
            + "\n"
            f"safety_policy_summary: {self.safety_policy_summary}\n"
            f"rule_nlu_result: {rule_result}\n"
            f"user_text: {self.normalized_text}"
        )
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]


@dataclass(frozen=True)
class LLMProviderResult:
    provider: str
    available: bool
    raw_output: str = ""
    latency_ms: float = 0.0
    error_type: str = ""
    error_message: str = ""
    model_status: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


LLMRequest = LLMProviderContext
LLMResponse = LLMProviderResult


class LLMProviderError(Exception):
    pass


class LLMProviderUnavailable(LLMProviderError):
    pass


class LLMProvider(Protocol):
    name: str

    def status(self) -> dict[str, Any]:
        ...

    def generate(self, context: LLMProviderContext) -> LLMProviderResult:
        ...


class DisabledLLMProvider:
    name = "disabled"

    def status(self) -> dict[str, Any]:
        return {"provider": self.name, "available": False, "reason": "disabled"}

    def generate(self, context: LLMProviderContext) -> LLMProviderResult:
        return LLMProviderResult(
            provider=self.name,
            available=False,
            error_type="disabled",
            error_message="LLM provider is disabled.",
            model_status=self.status(),
        )


class ReservedAPIProvider:
    def __init__(self, name: str):
        self.name = name

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.name,
            "available": False,
            "reason": "reserved_provider_not_implemented",
        }

    def generate(self, context: LLMProviderContext) -> LLMProviderResult:
        return LLMProviderResult(
            provider=self.name,
            available=False,
            error_type="reserved_provider",
            error_message=f"{self.name} is reserved for a future API provider.",
            model_status=self.status(),
        )
