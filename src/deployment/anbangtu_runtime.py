from __future__ import annotations

from typing import Any


class AnbangtuRuntime:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    def summary(self) -> dict[str, Any]:
        return {
            "target_system_name": self.config.get("target_system_name", "anbangtu"),
            "profile": self.config.get("profile", "pending-confirmation"),
            "os_type": self.config.get("os_type", "unknown"),
            "prefer_local_whisper": self.config.get("prefer_local_whisper", True),
            "prefer_local_qwen": self.config.get("prefer_local_qwen", False),
            "remote_asr_endpoint_configured": bool(self.config.get("remote_asr_endpoint")),
            "remote_qwen_endpoint_configured": bool(self.config.get("remote_qwen_endpoint")),
        }

    def choose_asr_mode(self) -> str:
        if self.config.get("prefer_local_whisper", True):
            return "local_whisper"
        if self.config.get("remote_asr_endpoint"):
            return "remote_asr"
        return "local_whisper"

    def choose_qwen_mode(self) -> str:
        if self.config.get("prefer_local_qwen", False):
            return "local_qwen"
        if self.config.get("remote_qwen_endpoint"):
            return "remote_qwen"
        return "configured_default"
