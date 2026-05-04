from __future__ import annotations

from src.commands.command_catalog import CommandCatalog
from src.models import RobotCommand, SemanticResult, new_command_id, utc_now_iso


class CommandNormalizer:
    def __init__(self, catalog: CommandCatalog):
        self.catalog = catalog

    def normalize(
        self,
        semantic: SemanticResult,
        source_text: str,
        command_id: str | None = None,
    ) -> RobotCommand:
        if not semantic.is_command:
            raise ValueError("non-command semantic result cannot be normalized")
        spec = self.catalog.get(semantic.intent)
        if spec is None:
            return RobotCommand(
                command_id=command_id or new_command_id(),
                intent=semantic.intent or "unknown",
                duration_sec=float(semantic.duration_sec or 0.0),
                speed=0.0,
                priority=0,
                source_text=source_text,
                created_at=utc_now_iso(),
            speed_level=semantic.speed_level or "slow",
            metadata={
                "normalization_error": "intent is not in command catalog",
                "risk_level": semantic.risk_level,
                "semantic_executable": semantic.executable,
                "rejected_by_nlu": semantic.rejected_by_nlu,
            },
        )
        duration = (
            float(semantic.duration_sec)
            if semantic.duration_sec is not None
            else spec.default_duration_sec
        )
        if not spec.requires_duration:
            duration = 0.0
        speed = spec.default_speed
        risk_level = semantic.risk_level if semantic.risk_level != "safe" else spec.risk_level
        return RobotCommand(
            command_id=command_id or new_command_id(),
            intent=semantic.intent,
            duration_sec=duration,
            speed=speed,
            priority=100 if semantic.intent == "stop" else 10,
            source_text=source_text,
            created_at=utc_now_iso(),
            speed_level=semantic.speed_level or "slow",
            metadata={
                "display_name": spec.display_name,
                "go2_action_type": spec.go2_action_type,
                "requires_duration": spec.requires_duration,
                "requested_speed_level": semantic.speed_level,
                "official_name": spec.official_name,
                "sdk_method": spec.sdk_method,
                "sdk_api_id": spec.sdk_api_id,
                "official_supported": spec.official_supported,
                "risk_level": risk_level,
                "catalog_risk_level": spec.risk_level,
                "voice_enabled": spec.voice_enabled,
                "mock_enabled": spec.mock_enabled,
                "real_robot_enabled": spec.real_robot_enabled,
                "requires_manual_confirm": spec.requires_manual_confirm,
                "sdk_args": list(spec.sdk_args or []),
                "semantic_executable": semantic.executable,
                "rejected_by_nlu": semantic.rejected_by_nlu,
            },
        )
