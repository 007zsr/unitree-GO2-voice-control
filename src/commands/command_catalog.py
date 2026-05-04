from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.commands.go2_action_catalog import Go2ActionCatalog, Go2ActionSpec


@dataclass(frozen=True)
class CommandSpec:
    intent: str
    display_name: str
    go2_action_type: str
    requires_duration: bool
    default_duration_sec: float
    max_duration_sec: float
    default_speed: float
    max_speed: float
    can_interrupt: bool
    requires_robot_standing: bool
    official_name: str = ""
    sdk_method: str = ""
    sdk_api_id: int | None = None
    official_supported: bool = False
    risk_level: str = "safe"
    voice_enabled: bool = True
    mock_enabled: bool = True
    real_robot_enabled: bool = False
    requires_manual_confirm: bool = False
    aliases: dict[str, list[str]] | None = None
    description_zh: str = ""
    description_en: str = ""
    reason: str = ""
    sdk_args: list[Any] | None = None
    derived_from: str = ""

    @classmethod
    def from_mapping(
        cls,
        intent: str,
        data: dict[str, Any],
        action: Go2ActionSpec | None = None,
    ) -> "CommandSpec":
        required = [
            "display_name",
            "go2_action_type",
            "requires_duration",
            "default_duration_sec",
            "max_duration_sec",
            "default_speed",
            "max_speed",
            "can_interrupt",
            "requires_robot_standing",
        ]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Command {intent!r} missing fields: {', '.join(missing)}")
        return cls(
            intent=intent,
            display_name=str(data["display_name"]),
            go2_action_type=str(data["go2_action_type"]),
            requires_duration=bool(data["requires_duration"]),
            default_duration_sec=float(data["default_duration_sec"]),
            max_duration_sec=float(data["max_duration_sec"]),
            default_speed=float(data["default_speed"]),
            max_speed=float(data["max_speed"]),
            can_interrupt=bool(data["can_interrupt"]),
            requires_robot_standing=bool(data["requires_robot_standing"]),
            official_name=action.official_name if action else str(data.get("official_name", "")),
            sdk_method=action.sdk_method if action else str(data.get("sdk_method", "")),
            sdk_api_id=action.sdk_api_id if action else data.get("sdk_api_id"),
            official_supported=action.official_supported if action else bool(data.get("official_supported", False)),
            risk_level=action.risk_level if action else str(data.get("risk_level", "safe")),
            voice_enabled=action.voice_enabled if action else bool(data.get("voice_enabled", True)),
            mock_enabled=action.mock_enabled if action else bool(data.get("mock_enabled", True)),
            real_robot_enabled=action.real_robot_enabled if action else bool(data.get("real_robot_enabled", False)),
            requires_manual_confirm=(
                action.requires_manual_confirm if action else bool(data.get("requires_manual_confirm", False))
            ),
            aliases=action.aliases if action else data.get("aliases", {"en": [], "zh": []}),
            description_zh=action.description_zh if action else str(data.get("description_zh", "")),
            description_en=action.description_en if action else str(data.get("description_en", "")),
            reason=action.reason if action else str(data.get("reason", "")),
            sdk_args=action.sdk_args if action else list(data.get("sdk_args", [])),
            derived_from=action.derived_from if action else str(data.get("derived_from", "")),
        )

    @classmethod
    def from_action(cls, action: Go2ActionSpec) -> "CommandSpec":
        return cls.from_mapping(action.intent, action.to_command_mapping(), action=action)


class CommandCatalog:
    def __init__(self, config: dict[str, Any], action_config: dict[str, Any] | None = None):
        self.action_catalog = Go2ActionCatalog(action_config)
        command_map = config.get("commands")
        if not isinstance(command_map, dict) or not command_map:
            raise ValueError("commands.yaml must contain a non-empty 'commands' mapping")
        self._commands = {
            intent: CommandSpec.from_mapping(intent, data, self.action_catalog.get(intent))
            for intent, data in command_map.items()
        }
        for action in self.action_catalog.actions():
            self._commands.setdefault(action.intent, CommandSpec.from_action(action))

    def get(self, intent: str) -> CommandSpec | None:
        return self._commands.get(intent)

    def require(self, intent: str) -> CommandSpec:
        spec = self.get(intent)
        if spec is None:
            raise ValueError(f"Unknown or non-whitelisted command intent: {intent}")
        return spec

    def is_allowed(self, intent: str) -> bool:
        return intent in self._commands

    def intents(self) -> list[str]:
        return list(self._commands.keys())

    def action_specs(self) -> list[Go2ActionSpec]:
        return self.action_catalog.actions()

    def aliases_for_intent(self, intent: str) -> dict[str, list[str]]:
        action = self.action_catalog.get(intent)
        if action:
            return action.aliases
        spec = self.get(intent)
        if spec and spec.aliases:
            return spec.aliases
        return {"zh": [], "en": []}
