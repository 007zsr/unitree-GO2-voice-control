from __future__ import annotations

import json
from typing import Any

from src.models import SemanticResult


class SemanticParseError(ValueError):
    pass


class SemanticParser:
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
    ]

    def parse(self, raw_output: str) -> SemanticResult:
        cleaned = self._strip_code_fence(raw_output)
        if any(token in cleaned for token in self.FORBIDDEN_TOKENS):
            raise SemanticParseError("Qwen output contained forbidden code or SDK tokens")
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise SemanticParseError(f"Qwen output was not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise SemanticParseError("Qwen output JSON must be an object")
        return self._from_mapping(data, raw_output)

    def _strip_code_fence(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                return "\n".join(lines[1:-1]).strip()
        return stripped

    def _from_mapping(self, data: dict[str, Any], raw_output: str) -> SemanticResult:
        if "commands" in data and isinstance(data.get("commands"), list) and data.get("commands"):
            first = data["commands"][0]
            if isinstance(first, dict):
                data = {
                    **data,
                    "intent": data.get("intent", first.get("intent", "unknown")),
                    "duration_sec": data.get("duration_sec", first.get("duration_sec")),
                    "speed_level": data.get("speed_level", first.get("speed_level", "slow")),
                    "confidence": data.get("confidence", first.get("confidence", 0.0)),
                    "need_clarification": data.get(
                        "need_clarification",
                        data.get("needs_confirmation", False),
                    ),
                    "dangerous": data.get("dangerous", False),
                    "reason": data.get("reason", "Qwen returned a command plan."),
                }
        required = [
            "is_command",
            "intent",
            "duration_sec",
            "speed_level",
            "confidence",
            "need_clarification",
            "dangerous",
            "reason",
        ]
        missing = [field for field in required if field not in data]
        if missing:
            raise SemanticParseError(f"Qwen JSON missing fields: {', '.join(missing)}")
        duration = data.get("duration_sec")
        return SemanticResult(
            is_command=bool(data.get("is_command")),
            intent=str(data.get("intent") or "unknown"),
            duration_sec=None if duration is None else float(duration),
            speed_level=str(data.get("speed_level") or "slow"),
            source_language=str(data.get("source_language") or "unknown"),
            confidence=float(data.get("confidence") or 0.0),
            need_clarification=bool(data.get("need_clarification")),
            dangerous=bool(data.get("dangerous")),
            risk_level=str(data.get("risk_level") or ("dangerous" if data.get("dangerous") else "safe")),
            executable=bool(data.get("executable", True)),
            rejected_by_nlu=bool(data.get("rejected_by_nlu", False)),
            reason=str(data.get("reason") or ""),
            raw_output=raw_output,
            raw_result=data,
        )
