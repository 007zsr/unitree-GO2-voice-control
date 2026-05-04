from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


RISK_LEVELS = {"safe", "caution", "dangerous", "disabled"}


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)


def _as_int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _aliases(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {"en": [], "zh": []}
    return {
        "en": [str(item).strip() for item in _list(value.get("en")) if str(item).strip()],
        "zh": [str(item).strip() for item in _list(value.get("zh")) if str(item).strip()],
    }


@dataclass(frozen=True)
class Go2ActionSpec:
    intent: str
    official_name: str
    sdk_method: str
    risk_level: str
    official_supported: bool = True
    sdk_api_id: int | None = None
    voice_enabled: bool = False
    mock_enabled: bool = True
    real_robot_enabled: bool = False
    requires_standing: bool = False
    requires_duration: bool = False
    default_duration_sec: float = 0.0
    max_duration_sec: float = 0.0
    default_speed: float = 0.0
    max_speed: float = 0.0
    can_interrupt: bool = True
    requires_manual_confirm: bool = False
    aliases: dict[str, list[str]] = field(default_factory=lambda: {"en": [], "zh": []})
    description_zh: str = ""
    description_en: str = ""
    reason: str = ""
    sdk_args: list[Any] = field(default_factory=list)
    derived_from: str = ""

    @classmethod
    def from_mapping(cls, intent: str, data: dict[str, Any]) -> "Go2ActionSpec":
        risk = str(data.get("risk_level", "disabled")).strip().lower()
        if risk not in RISK_LEVELS:
            raise ValueError(f"Go2 action {intent!r} has invalid risk_level: {risk!r}")
        return cls(
            intent=intent,
            official_name=str(data.get("official_name") or intent),
            sdk_method=str(data.get("sdk_method") or data.get("official_name") or ""),
            risk_level=risk,
            official_supported=_as_bool(data.get("official_supported"), True),
            sdk_api_id=_as_int_or_none(data.get("sdk_api_id")),
            voice_enabled=_as_bool(data.get("voice_enabled"), False),
            mock_enabled=_as_bool(data.get("mock_enabled"), True),
            real_robot_enabled=_as_bool(data.get("real_robot_enabled"), False),
            requires_standing=_as_bool(data.get("requires_standing"), False),
            requires_duration=_as_bool(data.get("requires_duration"), False),
            default_duration_sec=_as_float(data.get("default_duration_sec"), 0.0),
            max_duration_sec=_as_float(data.get("max_duration_sec"), 0.0),
            default_speed=_as_float(data.get("default_speed"), 0.0),
            max_speed=_as_float(data.get("max_speed"), 0.0),
            can_interrupt=_as_bool(data.get("can_interrupt"), True),
            requires_manual_confirm=_as_bool(data.get("requires_manual_confirm"), False),
            aliases=_aliases(data.get("aliases")),
            description_zh=str(data.get("description_zh") or ""),
            description_en=str(data.get("description_en") or ""),
            reason=str(data.get("reason") or ""),
            sdk_args=_list(data.get("sdk_args")),
            derived_from=str(data.get("derived_from") or ""),
        )

    def all_aliases(self) -> list[str]:
        return [*self.aliases.get("en", []), *self.aliases.get("zh", [])]

    def to_command_mapping(self) -> dict[str, Any]:
        return {
            "display_name": self.description_en or self.official_name or self.intent,
            "go2_action_type": self.intent,
            "requires_duration": self.requires_duration,
            "default_duration_sec": self.default_duration_sec,
            "max_duration_sec": self.max_duration_sec,
            "default_speed": self.default_speed,
            "max_speed": self.max_speed,
            "can_interrupt": self.can_interrupt,
            "requires_robot_standing": self.requires_standing,
        }


@dataclass(frozen=True)
class ActionAliasMatch:
    action: Go2ActionSpec
    alias: str
    language: str
    confidence: float


class Go2ActionCatalog:
    def __init__(self, config: dict[str, Any] | None = None):
        raw_actions = (config or {}).get("actions", {})
        if not isinstance(raw_actions, dict):
            raw_actions = {}
        self._actions: dict[str, Go2ActionSpec] = {
            str(intent): Go2ActionSpec.from_mapping(str(intent), data)
            for intent, data in raw_actions.items()
            if isinstance(data, dict)
        }

    def get(self, intent: str) -> Go2ActionSpec | None:
        return self._actions.get(intent)

    def require(self, intent: str) -> Go2ActionSpec:
        action = self.get(intent)
        if action is None:
            raise ValueError(f"Unknown Go2 action intent: {intent}")
        return action

    def actions(self) -> list[Go2ActionSpec]:
        return list(self._actions.values())

    def intents(self) -> list[str]:
        return list(self._actions.keys())

    def aliases_for_intent(self, intent: str) -> dict[str, list[str]]:
        action = self.get(intent)
        return action.aliases if action else {"en": [], "zh": []}

    def sequence_keywords(self) -> tuple[list[str], list[str]]:
        en: list[str] = []
        zh: list[str] = []
        for action in self.actions():
            en.extend(action.aliases.get("en", []))
            zh.extend(action.aliases.get("zh", []))
        return sorted(set(en), key=len, reverse=True), sorted(set(zh), key=len, reverse=True)

    def match_text(self, text: str) -> ActionAliasMatch | None:
        original = " ".join(str(text or "").strip().split())
        if not original:
            return None
        lowered = original.lower()
        matches: list[ActionAliasMatch] = []
        for action in self.actions():
            for language, aliases in action.aliases.items():
                for alias in aliases:
                    if self._matches_alias(original, lowered, alias, language):
                        matches.append(
                            ActionAliasMatch(
                                action=action,
                                alias=alias,
                                language=language,
                                confidence=self._confidence_for(action, alias),
                            )
                        )
        if not matches:
            return None
        return sorted(matches, key=lambda item: (len(item.alias), item.confidence), reverse=True)[0]

    def _matches_alias(self, original: str, lowered: str, alias: str, language: str) -> bool:
        clean_alias = alias.strip()
        if not clean_alias:
            return False
        if language == "zh" or re.search(r"[\u4e00-\u9fff]", clean_alias):
            return clean_alias in original
        pattern = r"\b" + r"\s+".join(re.escape(part) for part in clean_alias.lower().split()) + r"\b"
        return bool(re.search(pattern, lowered))

    def _confidence_for(self, action: Go2ActionSpec, alias: str) -> float:
        if action.risk_level == "dangerous":
            return 0.95
        if action.risk_level == "disabled":
            return 0.90
        if len(alias.split()) >= 2 or re.search(r"[\u4e00-\u9fff]", alias):
            return 0.92
        return 0.86
