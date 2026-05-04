from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_command_id() -> str:
    return f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"


def new_plan_id() -> str:
    return f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"


@dataclass
class TranscriptResult:
    text: str
    language: str = ""
    duration_sec: float = 0.0
    no_speech_prob: float = 1.0
    language_config: str = ""
    task: str = "transcribe"
    audio_path: str = ""
    audio_file_size: int = 0
    sample_rate: int = 0
    channels: int = 0
    peak_amplitude: float = 0.0
    rms_amplitude: float = 0.0
    is_silent_like: bool = False
    error_message: str = ""
    whisper_model: str = ""
    whisper_model_dir: str = ""
    whisper_loaded: bool = False
    whisper_executed: bool = False
    segments_count: int = 0
    segments_text_preview: list[str] = field(default_factory=list)
    raw_result_keys: list[str] = field(default_factory=list)
    text_empty: bool = False
    segments_empty: bool = False
    reason_guess: str = ""
    raw_result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticResult:
    is_command: bool
    intent: str
    duration_sec: float | None = None
    speed_level: str = "slow"
    source_language: str = "unknown"
    confidence: float = 0.0
    need_clarification: bool = False
    dangerous: bool = False
    risk_level: str = "safe"
    executable: bool = True
    rejected_by_nlu: bool = False
    reason: str = ""
    raw_output: str = ""
    raw_result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RobotCommand:
    command_id: str
    intent: str
    duration_sec: float
    speed: float
    priority: int
    source_text: str
    created_at: str
    speed_level: str = "slow"
    metadata: dict[str, Any] = field(default_factory=dict)
    sequence_index: int = 1
    sequence_total: int = 1
    source_span: str = ""
    inferred: bool = False
    inference_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CommandPlan:
    plan_id: str
    session_id: str
    source_text: str
    source_language: str
    parse_mode: str
    commands: list[RobotCommand]
    confidence: float
    needs_confirmation: bool
    reason: str
    created_at: str = field(default_factory=utc_now_iso)
    plan_type: str = "single"
    truncated: bool = False
    truncated_count: int = 0
    fuzzy_detected: bool = False
    dedup_signature: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["commands"] = [command.to_dict() for command in self.commands]
        return data

    @property
    def intent_sequence(self) -> list[str]:
        return [command.intent for command in self.commands]


@dataclass
class SafetyDecision:
    allowed: bool
    reason: str
    normalized_command: RobotCommand | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.normalized_command is not None:
            data["normalized_command"] = self.normalized_command.to_dict()
        return data


@dataclass
class RobotState:
    connected: bool = False
    standing: bool = True
    mode: str = "unknown"
    battery: float | None = None
    raw_state: dict[str, Any] = field(default_factory=dict)
    last_update: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RobotActionResult:
    success: bool
    command_id: str
    message: str
    raw_response: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CommandFlowResult:
    command_id: str
    accepted: bool
    stage: str
    message: str
    transcript: TranscriptResult | None = None
    semantic: SemanticResult | None = None
    command: RobotCommand | None = None
    safety: SafetyDecision | None = None
    queue_status: str | None = None
    command_plan: CommandPlan | None = None
    plan_results: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "accepted": self.accepted,
            "stage": self.stage,
            "message": self.message,
            "transcript": self.transcript.to_dict() if self.transcript else None,
            "semantic": self.semantic.to_dict() if self.semantic else None,
            "command": self.command.to_dict() if self.command else None,
            "safety": self.safety.to_dict() if self.safety else None,
            "queue_status": self.queue_status,
            "command_plan": self.command_plan.to_dict() if self.command_plan else None,
            "plan_results": self.plan_results,
        }

    def to_pretty_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class PipelineDebugResult:
    input_type: str
    command_id: str
    accepted: bool
    stage: str
    message: str
    transcript_text: str = ""
    asr_diagnostics: dict[str, Any] | None = None
    semantic_result: dict[str, Any] | None = None
    command_plan: dict[str, Any] | None = None
    robot_command: dict[str, Any] | None = None
    safety_decision: dict[str, Any] | None = None
    queue_result: str | None = None
    adapter_result: dict[str, Any] | None = None
    error_stage: str | None = None
    error_message: str | None = None
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_pretty_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
