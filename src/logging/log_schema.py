from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.models import utc_now_iso


@dataclass
class PipelineLogRecord:
    timestamp: str = field(default_factory=utc_now_iso)
    session_id: str = ""
    command_id: str = ""
    listen_id: str = ""
    chunk_id: str = ""
    mode: str = ""
    source_type: str = ""
    stage: str = ""
    status: str = ""
    message: str = ""
    transcript_text: str = ""
    semantic_result: dict[str, Any] | None = None
    command_plan: dict[str, Any] | None = None
    robot_command: dict[str, Any] | None = None
    safety_decision: dict[str, Any] | None = None
    queue_result: Any = None
    adapter_result: dict[str, Any] | None = None
    audio_debug_path: str = ""
    asr_diagnostics: dict[str, Any] | None = None
    error_stage: str = ""
    error_message: str = ""
    duration_ms: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
