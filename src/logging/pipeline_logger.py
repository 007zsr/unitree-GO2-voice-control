from __future__ import annotations

import json
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from typing import Any

from src.logging.log_paths import LogPaths, build_log_paths
from src.logging.log_schema import PipelineLogRecord
from src.models import PipelineDebugResult, utc_now_iso


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _date_dir() -> str:
    return datetime.now().strftime("%Y%m%d")


def new_session_id() -> str:
    return f"session_{_stamp()}_{uuid4().hex[:6]}"


def new_listen_id() -> str:
    return f"listen_{_stamp()}_{uuid4().hex[:6]}"


def new_chunk_id() -> str:
    return f"chunk_{_stamp()}_{uuid4().hex[:6]}"


@dataclass
class ContinuousRun:
    listen_id: str
    started_at: str
    directory: Path
    listening_session_path: Path
    chunks_path: Path
    commands_path: Path
    errors_path: Path
    summary_path: Path
    chunk_count: int = 0
    silent_count: int = 0
    asr_success_count: int = 0
    asr_empty_count: int = 0
    non_command_count: int = 0
    command_count: int = 0
    plans_detected_count: int = 0
    plans_executed_count: int = 0
    plans_skipped_duplicate_count: int = 0
    fuzzy_plans_detected_count: int = 0
    plans_need_confirmation_count: int = 0
    duplicate_skipped_count: int = 0
    ambiguous_rejected_count: int = 0
    strict_rejected_count: int = 0
    safety_rejected_count: int = 0
    execution_success_count: int = 0
    adapter_failed_count: int = 0
    error_count: int = 0
    extra_counts: dict[str, int] = field(default_factory=dict)


class PipelineLogger:
    def __init__(self, root_dir: str | Path, project_root: str | Path | None = None):
        self.paths: LogPaths = build_log_paths(root_dir)
        self.project_root = Path(project_root).resolve() if project_root else None
        self.session_id = new_session_id()
        self.session_path = self.paths.gui_sessions / _date_dir() / f"{self.session_id}.jsonl"
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self.current_task_path: Path | None = None
        self.current_continuous: ContinuousRun | None = None
        self._lock = threading.RLock()

    def start_gui_session(self, environment: dict[str, Any] | None = None) -> None:
        self.log_gui_event(
            "session_started",
            status="started",
            stage="gui",
            source_type="system",
            extra={
                "python_executable": sys.executable,
                **(environment or {}),
            },
        )
        self._write_index(
            {
                "timestamp": utc_now_iso(),
                "session_id": self.session_id,
                "mode": "gui_session",
                "status": "started",
                "log_path": self._display_path(self.session_path),
                "summary": "GUI session started",
            }
        )

    def end_gui_session(self) -> None:
        if self.current_continuous is not None:
            self.end_continuous_listening("gui shutdown")
        self.log_gui_event("session_ended", status="success", stage="gui", source_type="system")
        self._write_index(
            {
                "timestamp": utc_now_iso(),
                "session_id": self.session_id,
                "mode": "gui_session",
                "status": "ended",
                "log_path": self._display_path(self.session_path),
                "summary": "GUI session ended",
            }
        )

    def log_gui_event(
        self,
        message: str,
        status: str = "success",
        stage: str = "gui",
        source_type: str = "gui_button",
        extra: dict[str, Any] | None = None,
    ) -> None:
        record = PipelineLogRecord(
            session_id=self.session_id,
            mode="gui_session",
            source_type=source_type,
            stage=stage,
            status=status,
            message=message,
            extra=extra or {},
        )
        self._append_jsonl(self.session_path, record.to_dict())

    def start_command(self, command_id: str, mode: str, source_type: str, message: str = "command started") -> Path:
        task_path = self.paths.one_shot / _date_dir() / f"{command_id}.jsonl"
        task_path.parent.mkdir(parents=True, exist_ok=True)
        self.current_task_path = task_path
        self.log_stage(
            task_path,
            command_id=command_id,
            mode=mode,
            source_type=source_type,
            stage="gui",
            status="started",
            message=message,
        )
        return task_path

    def log_stage(
        self,
        task_path: str | Path,
        command_id: str,
        mode: str,
        source_type: str,
        stage: str,
        status: str,
        message: str = "",
        **payload: Any,
    ) -> None:
        self._append_jsonl(
            Path(task_path),
            PipelineLogRecord(
                session_id=self.session_id,
                command_id=command_id,
                mode=mode,
                source_type=source_type,
                stage=stage,
                status=status,
                message=message,
                transcript_text=str(payload.pop("transcript_text", "") or ""),
                semantic_result=payload.pop("semantic_result", None),
                robot_command=payload.pop("robot_command", None),
                safety_decision=payload.pop("safety_decision", None),
                queue_result=payload.pop("queue_result", None),
                adapter_result=payload.pop("adapter_result", None),
                audio_debug_path=self._display_path(payload.pop("audio_debug_path", "") or ""),
                asr_diagnostics=payload.pop("asr_diagnostics", None),
                error_stage=str(payload.pop("error_stage", "") or ""),
                error_message=str(payload.pop("error_message", "") or ""),
                duration_ms=payload.pop("duration_ms", None),
                extra=payload,
            ).to_dict(),
        )

    def finish_command(
        self,
        task_path: str | Path,
        command_id: str,
        mode: str,
        source_type: str,
        status: str,
        message: str,
    ) -> None:
        self.log_stage(
            task_path,
            command_id=command_id,
            mode=mode,
            source_type=source_type,
            stage="complete",
            status=status,
            message=message,
        )

    def log_one_shot_result(self, result: PipelineDebugResult, source_type: str) -> Path:
        command_id = result.command_id or f"cmd_{_stamp()}_{uuid4().hex[:6]}"
        mode = "one_shot_voice" if "audio" in result.input_type or "voice" in result.input_type else "one_shot_text"
        task_path = self.paths.one_shot / _date_dir() / f"{command_id}.jsonl"
        task_path.parent.mkdir(parents=True, exist_ok=True)
        self.current_task_path = task_path

        self._append_jsonl(
            task_path,
            PipelineLogRecord(
                session_id=self.session_id,
                command_id=command_id,
                mode=mode,
                source_type=source_type,
                stage="gui",
                status="started",
                message="one-shot task started",
            ).to_dict(),
        )
        for record in self._records_from_debug_result(result, command_id, mode, source_type):
            self._append_jsonl(task_path, record.to_dict())
        final_status = "success" if result.accepted else "rejected"
        if self._is_system_error_stage(result.error_stage):
            final_status = "failed"
        self._append_jsonl(
            task_path,
            PipelineLogRecord(
                session_id=self.session_id,
                command_id=command_id,
                mode=mode,
                source_type=source_type,
                stage="complete",
                status=final_status,
                message=result.message,
            ).to_dict(),
        )
        self._write_index(
            {
                "timestamp": utc_now_iso(),
                "session_id": self.session_id,
                "command_id": command_id,
                "mode": mode,
                "status": final_status,
                "log_path": self._display_path(task_path),
                "summary": result.message,
            }
        )
        if self._is_system_error_stage(result.error_stage):
            self.log_error(result.error_stage, result.error_message or result.message, command_id=command_id, mode=mode)
        return task_path

    def start_continuous_listening(
        self,
        config: dict[str, Any] | None = None,
        audio_status: dict[str, Any] | None = None,
        asr_status: dict[str, Any] | None = None,
    ) -> ContinuousRun:
        listen_id = new_listen_id()
        directory = self.paths.continuous / _date_dir() / listen_id
        directory.mkdir(parents=True, exist_ok=True)
        run = ContinuousRun(
            listen_id=listen_id,
            started_at=utc_now_iso(),
            directory=directory,
            listening_session_path=directory / "listening_session.jsonl",
            chunks_path=directory / "chunks.jsonl",
            commands_path=directory / "commands.jsonl",
            errors_path=directory / "errors.jsonl",
            summary_path=directory / "summary.md",
        )
        self.current_continuous = run
        self._append_jsonl(
            run.listening_session_path,
            PipelineLogRecord(
                session_id=self.session_id,
                listen_id=listen_id,
                mode="continuous_listening",
                source_type="gui_button",
                stage="gui",
                status="started",
                message="continuous listening started",
                extra={
                    "config": config or {},
                    "audio_status": audio_status or {},
                    "asr_status": asr_status or {},
                },
            ).to_dict(),
        )
        self._write_index(
            {
                "timestamp": utc_now_iso(),
                "session_id": self.session_id,
                "listen_id": listen_id,
                "mode": "continuous_listening",
                "status": "started",
                "log_path": self._display_path(directory),
                "summary": "continuous listening started",
            }
        )
        return run

    def end_continuous_listening(self, message: str = "continuous listening stopped") -> None:
        run = self.current_continuous
        if run is None:
            return
        self._append_jsonl(
            run.listening_session_path,
            PipelineLogRecord(
                session_id=self.session_id,
                listen_id=run.listen_id,
                mode="continuous_listening",
                source_type="gui_button",
                stage="gui",
                status="success",
                message=message,
                extra={"started_at": run.started_at, "ended_at": utc_now_iso()},
            ).to_dict(),
        )
        run.summary_path.write_text(self._continuous_summary(run), encoding="utf-8")
        self._write_index(
            {
                "timestamp": utc_now_iso(),
                "session_id": self.session_id,
                "listen_id": run.listen_id,
                "mode": "continuous_listening",
                "status": "ended",
                "log_path": self._display_path(run.directory),
                "summary": (
                    f"chunks={run.chunk_count}, commands={run.command_count}, "
                    f"safety_rejected={run.safety_rejected_count}, errors={run.error_count}"
                ),
            }
        )
        self.current_continuous = None

    def log_continuous_chunk(self, chunk: dict[str, Any]) -> None:
        run = self.current_continuous
        if run is None:
            return
        chunk_id = str(chunk.get("chunk_id") or new_chunk_id())
        status = str(chunk.get("chunk_status") or "unknown")
        run.chunk_count += 1
        run.extra_counts[status] = run.extra_counts.get(status, 0) + 1
        if status == "skipped_silent":
            run.silent_count += 1
        elif status == "asr_success":
            run.asr_success_count += 1
        elif status == "non_command":
            run.asr_success_count += 1
            run.non_command_count += 1
        elif status == "command_detected":
            run.asr_success_count += 1
            run.command_count += 1
        elif status == "asr_empty":
            run.asr_empty_count += 1
        elif status == "duplicate_skipped":
            run.duplicate_skipped_count += 1
        elif status == "ambiguous_rejected":
            run.ambiguous_rejected_count += 1
        elif status == "strict_rejected":
            run.strict_rejected_count += 1
        elif status == "error":
            run.error_count += 1
        self._append_jsonl(
            run.chunks_path,
            PipelineLogRecord(
                session_id=self.session_id,
                listen_id=run.listen_id,
                chunk_id=chunk_id,
                mode="continuous_listening",
                source_type="voice_chunk",
                stage="audio",
                status=status,
                message=str(chunk.get("message") or status),
                audio_debug_path=self._display_path(chunk.get("audio_debug_path") or ""),
                asr_diagnostics=chunk.get("asr_diagnostics"),
                extra={k: v for k, v in chunk.items() if k not in {"chunk_id", "chunk_status", "message", "audio_debug_path", "asr_diagnostics"}},
            ).to_dict(),
        )

    def log_continuous_result(self, result: PipelineDebugResult) -> None:
        run = self.current_continuous
        if run is None:
            return
        semantic = result.semantic_result or {}
        is_command = bool(semantic.get("is_command"))
        if is_command:
            plan = result.command_plan or {}
            if plan:
                run.plans_detected_count += 1
                if len(plan.get("commands") or []) > 1:
                    run.extra_counts["multi_command_plan"] = run.extra_counts.get("multi_command_plan", 0) + 1
                if plan.get("fuzzy_detected"):
                    run.fuzzy_plans_detected_count += 1
                if plan.get("needs_confirmation"):
                    run.plans_need_confirmation_count += 1
            if result.stage == "deduplicate" and plan:
                run.plans_skipped_duplicate_count += 1
            if result.safety_decision and result.safety_decision.get("allowed") is False:
                run.safety_rejected_count += 1
            if result.accepted and plan:
                run.plans_executed_count += 1
            if result.adapter_result and result.adapter_result.get("success"):
                run.execution_success_count += 1
            if result.adapter_result and isinstance(result.adapter_result.get("plan_results"), list):
                for item in result.adapter_result.get("plan_results") or []:
                    adapter_result = item.get("adapter_result") if isinstance(item, dict) else None
                    if isinstance(adapter_result, dict) and adapter_result.get("success"):
                        run.execution_success_count += 1
            if result.adapter_result and result.adapter_result.get("success") is False:
                run.adapter_failed_count += 1
            records = self._records_from_debug_result(
                result,
                result.command_id,
                "continuous_listening",
                "voice_chunk",
                run.listen_id,
            )
            for record in records:
                self._append_jsonl(run.commands_path, record.to_dict())
        if self._is_system_error_stage(result.error_stage):
            run.error_count += 1
            self._append_jsonl(
                run.errors_path,
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=result.command_id,
                    listen_id=run.listen_id,
                    mode="continuous_listening",
                    source_type="voice_chunk",
                    stage="error",
                    status="failed",
                    message=result.message,
                    error_stage=result.error_stage or "",
                    error_message=result.error_message or "",
                ).to_dict(),
            )
            self.log_error(
                result.error_stage or "continuous",
                result.error_message or result.message,
                command_id=result.command_id,
                listen_id=run.listen_id,
                mode="continuous_listening",
            )

    def log_error(
        self,
        error_stage: str,
        error_message: str,
        command_id: str = "",
        listen_id: str = "",
        mode: str = "",
        extra: dict[str, Any] | None = None,
    ) -> None:
        error_path = self.paths.errors / f"errors_{_date_dir()}.jsonl"
        self._append_jsonl(
            error_path,
            PipelineLogRecord(
                session_id=self.session_id,
                command_id=command_id,
                listen_id=listen_id,
                mode=mode,
                source_type="system",
                stage="error",
                status="failed",
                message=error_message,
                error_stage=error_stage,
                error_message=error_message,
                extra=extra or {},
            ).to_dict(),
        )

    def get_current_log_paths(self) -> dict[str, str]:
        run = self.current_continuous
        return {
            "session_id": self.session_id,
            "session_log": self._display_path(self.session_path),
            "current_task_log": self._display_path(self.current_task_path) if self.current_task_path else "",
            "current_continuous_log": self._display_path(run.directory) if run else "",
            "index_log": self._display_path(self.paths.index / "log_index.jsonl"),
        }

    def _records_from_debug_result(
        self,
        result: PipelineDebugResult,
        command_id: str,
        mode: str,
        source_type: str,
        listen_id: str = "",
    ) -> list[PipelineLogRecord]:
        records: list[PipelineLogRecord] = []
        if result.asr_diagnostics:
            audio_path = self._display_path(result.asr_diagnostics.get("audio_path", ""))
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="audio_record",
                    status="success" if audio_path else "skipped",
                    message="audio debug file recorded" if audio_path else "no audio debug file",
                    audio_debug_path=audio_path,
                )
            )
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="audio_diagnostics",
                    status="success" if not result.asr_diagnostics.get("error_message") else "failed",
                    message=str(result.asr_diagnostics.get("error_message") or "audio diagnostics captured"),
                    audio_debug_path=audio_path,
                    asr_diagnostics=result.asr_diagnostics,
                )
            )
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="asr",
                    status="success" if result.transcript_text else "failed",
                    message=result.transcript_text or result.message,
                    transcript_text=result.transcript_text,
                    audio_debug_path=audio_path,
                    asr_diagnostics=result.asr_diagnostics,
                    error_stage=result.error_stage or "",
                    error_message=result.error_message or "",
                )
            )
        elif result.transcript_text:
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="input_text",
                    status="success",
                    message="text input received",
                    transcript_text=result.transcript_text,
                )
            )
        if result.semantic_result:
            semantic = result.semantic_result
            llm_extra = self._llm_fields_from_semantic(semantic)
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="nlu",
                    status="success" if semantic.get("is_command") else "skipped",
                    message=str(semantic.get("reason") or ""),
                    transcript_text=result.transcript_text,
                    semantic_result=semantic,
                    extra=llm_extra,
                )
            )
        if result.command_plan:
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="command_plan",
                    status="accepted" if not result.command_plan.get("needs_confirmation") else "rejected",
                    message=str(result.command_plan.get("reason") or ""),
                    transcript_text=result.transcript_text,
                    command_plan=result.command_plan,
                    extra={
                        "plan_type": result.command_plan.get("plan_type"),
                        "commands_count": len(result.command_plan.get("commands") or []),
                        "intent_sequence": result.command_plan.get("commands")
                        and [item.get("intent") for item in result.command_plan.get("commands")],
                        "fuzzy_detected": result.command_plan.get("fuzzy_detected"),
                        "needs_confirmation": result.command_plan.get("needs_confirmation"),
                        "truncated": result.command_plan.get("truncated"),
                        "dedup_signature": result.command_plan.get("dedup_signature"),
                    },
                )
            )
        if result.robot_command:
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="command_normalize",
                    status="success",
                    message="RobotCommand normalized",
                    robot_command=result.robot_command,
                )
            )
        if result.safety_decision:
            allowed = bool(result.safety_decision.get("allowed"))
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="safety",
                    status="accepted" if allowed else "rejected",
                    message=str(result.safety_decision.get("reason") or result.message),
                    safety_decision=result.safety_decision,
                    extra={
                        "event_type": "safety_accepted" if allowed else "safety_rejected",
                        "safety_reason": str(result.safety_decision.get("reason") or ""),
                    },
                )
            )
        if result.queue_result is not None:
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="queue",
                    status="accepted" if result.accepted else "rejected",
                    message=str(result.queue_result),
                    queue_result=result.queue_result,
                )
            )
        if result.adapter_result:
            adapter_success = bool(result.adapter_result.get("success"))
            if isinstance(result.adapter_result.get("plan_results"), list):
                plan_results = result.adapter_result.get("plan_results") or []
                adapter_success = bool(plan_results) and all(
                    not isinstance(item, dict)
                    or not isinstance(item.get("adapter_result"), dict)
                    or bool(item["adapter_result"].get("success"))
                    for item in plan_results
                )
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="adapter",
                    status="success" if adapter_success else "failed",
                    message=str(result.adapter_result.get("message") or "adapter results captured"),
                    adapter_result=result.adapter_result,
                )
            )
        if result.error_stage == "safety":
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="safety_rejected",
                    status="rejected",
                    message=f"Safety rejected: {result.error_message or result.message}",
                    extra={
                        "event_type": "safety_rejected",
                        "safety_reason": result.error_message or result.message,
                    },
                )
            )
        elif result.error_stage:
            records.append(
                PipelineLogRecord(
                    session_id=self.session_id,
                    command_id=command_id,
                    listen_id=listen_id,
                    mode=mode,
                    source_type=source_type,
                    stage="error",
                    status="failed",
                    message=result.error_message or result.message,
                    error_stage=result.error_stage or "",
                    error_message=result.error_message or "",
                )
            )
        return records

    def _continuous_summary(self, run: ContinuousRun) -> str:
        lines = [
            f"# Continuous Listening Summary: {run.listen_id}",
            "",
            f"- Session ID: {self.session_id}",
            f"- Start time: {run.started_at}",
            f"- End time: {utc_now_iso()}",
            f"- Total chunks: {run.chunk_count}",
            f"- Silent skipped: {run.silent_count}",
            f"- ASR success: {run.asr_success_count}",
            f"- ASR empty: {run.asr_empty_count}",
            f"- Non-command: {run.non_command_count}",
            f"- Commands: {run.command_count}",
            f"- Plans detected: {run.plans_detected_count}",
            f"- Plans executed: {run.plans_executed_count}",
            f"- Plans skipped duplicate: {run.plans_skipped_duplicate_count}",
            f"- Fuzzy plans detected: {run.fuzzy_plans_detected_count}",
            f"- Plans need confirmation: {run.plans_need_confirmation_count}",
            f"- Duplicate skipped: {run.duplicate_skipped_count}",
            f"- Ambiguous rejected: {run.ambiguous_rejected_count}",
            f"- Strict rejected: {run.strict_rejected_count}",
            f"- Safety rejected: {run.safety_rejected_count}",
            f"- Executed success: {run.execution_success_count}",
            f"- Adapter failed: {run.adapter_failed_count}",
            f"- System errors: {run.error_count}",
            f"- Error count: {run.error_count}",
            "",
            "## Chunk Status Counts",
        ]
        for key, value in sorted(run.extra_counts.items()):
            lines.append(f"- {key}: {value}")
        return "\n".join(lines) + "\n"

    def _is_system_error_stage(self, stage: str | None) -> bool:
        if not stage:
            return False
        return stage not in {
            "asr",
            "semantic",
            "semantic_debug",
            "confirmation",
            "safety",
            "deduplicate",
            "audio_dependency",
            "asr_dependency",
            "audio_busy",
        }

    def _llm_fields_from_semantic(self, semantic: dict[str, Any]) -> dict[str, Any]:
        raw = semantic.get("raw_result")
        if not isinstance(raw, dict):
            return {}
        keys = [
            "semantic_engine_mode",
            "llm_enabled",
            "llm_provider",
            "llm_model_dir",
            "llm_available",
            "fallback_triggered",
            "fallback_reason",
            "llm_input_text",
            "llm_raw_output",
            "llm_parsed_intent",
            "llm_confidence",
            "llm_needs_confirmation",
            "llm_risk",
            "llm_latency_ms",
            "llm_error_type",
            "final_semantic_source",
        ]
        return {key: raw.get(key) for key in keys if key in raw}

    def _write_index(self, record: dict[str, Any]) -> None:
        self._append_jsonl(self.paths.index / "log_index.jsonl", record)

    def _append_jsonl(self, path: Path, record: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._sanitize(record)
        with self._lock:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, Path):
            return self._display_path(value)
        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for key, item in value.items():
                lowered = str(key).lower()
                if any(token in lowered for token in ["key", "token", "secret", "password"]):
                    result[key] = "***"
                elif key == "raw_result":
                    result[key] = "<omitted>"
                else:
                    result[key] = self._sanitize(item)
            return result
        if isinstance(value, list):
            return [self._sanitize(item) for item in value[:50]]
        if isinstance(value, str):
            text = self._display_path(value)
            return text if len(text) <= 2000 else text[:2000] + "...<truncated>"
        return value

    def _display_path(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value)
        if not text:
            return ""
        path = Path(text)
        if self.project_root is not None:
            try:
                return str(path.resolve().relative_to(self.project_root))
            except (OSError, ValueError):
                return text
        return text
