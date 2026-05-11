from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Callable

from src.asr.asr_env import (
    AsrDependencyStatus,
    check_asr_dependencies,
    resolve_project_path,
    resolve_whisper_model_dir,
)
from src.audio.audio_env import AudioDependencyStatus, check_audio_dependencies
from src.config import ConfigSet, deep_merge, load_yaml, write_yaml
from src.gui.listening_worker import ContinuousListeningWorker, OneShotVoiceWorker
from src.logging.pipeline_logger import PipelineLogger
from src.models import CommandFlowResult, PipelineDebugResult, new_command_id, utc_now_iso
from src.nlu.llm_provider_factory import build_llm_provider
from src.nlu.local_qwen_provider import check_local_qwen_model
from src.nlu.semantic_engine_config import semantic_engine_config
from src.runtime.session_runtime import SessionRuntime
from src.runtime.runtime_overrides import apply_runtime_overrides


DebugCallback = Callable[[PipelineDebugResult], None]
EventCallback = Callable[[str], None]


class GuiRuntimeBridge:
    def __init__(
        self,
        config_dir: str | Path | None = None,
        runtime_overrides: dict[str, object] | None = None,
    ):
        self.configs = ConfigSet.load(config_dir)
        apply_runtime_overrides(self.configs, runtime_overrides)
        self.runtime = SessionRuntime(self.configs)
        self._started = False
        self._listener: ContinuousListeningWorker | None = None
        self._one_shot: OneShotVoiceWorker | None = None
        self._last_audio_status = check_audio_dependencies(query_devices=False)
        self._last_asr_status = self._check_asr_status()
        self._audio_state = "idle"
        self._audio_lock = threading.Lock()
        log_config = self.configs.app.get("logging", {})
        log_root = Path(str(log_config.get("root_dir") or self.configs.app.get("log_dir", "runtime_data/logs")))
        if not log_root.is_absolute():
            log_root = self.configs.config_dir.parent / log_root
        self.pipeline_logger = PipelineLogger(log_root, project_root=self.configs.config_dir.parent)
        self.pipeline_logger.start_gui_session(
            {
                "robot_mode": self.configs.robot_mode,
                "enable_real_robot": self.configs.enable_real_robot,
                "audio_status": self._last_audio_status.to_dict(),
                "asr_status": self._last_asr_status.to_dict(),
                "qwen": self.configs.models.get("qwen", {}),
                "semantic_engine": self.runtime.semantic_engine_config,
                "asr": self.configs.models.get("asr", {}),
                "settings": self.get_settings(),
                "real_demo": self.real_demo_settings(),
            }
        )

    def start(self) -> None:
        if self._started:
            return
        self.runtime.start()
        self._started = True
        self.pipeline_logger.log_gui_event("runtime started", extra=self.runtime.get_current_status())

    def shutdown(self) -> None:
        self.stop_continuous_listening()
        if self._one_shot and self._one_shot.is_alive():
            self._one_shot.join(timeout=5)
        if self._started:
            self.runtime.shutdown()
            self._started = False
        self.pipeline_logger.end_gui_session()

    def process_text_once(self, text: str, input_type: str = "text") -> PipelineDebugResult:
        try:
            before_state = self._capture_real_demo_state("before")
            flow = self.runtime.process_text(text)
            result = self._to_debug_result(input_type, flow)
            after_state = self._capture_real_demo_state("after")
            self._attach_real_demo_state(result, before_state, after_state)
            self._log_real_demo_command(result, before_state, after_state)
            self.pipeline_logger.log_one_shot_result(result, "text")
            return result
        except Exception as exc:
            result = self._exception_debug(input_type, "text", exc)
            self.pipeline_logger.log_one_shot_result(result, "text")
            return result

    def process_audio_once(self, audio_path: str | Path, input_type: str = "audio") -> PipelineDebugResult:
        status = self.get_audio_status()
        if not status.available:
            result = self.audio_dependency_result(input_type)
            self._log_audio_result(input_type, result)
            return result
        asr_status = self.get_asr_status()
        if not asr_status.available:
            result = self.asr_dependency_result(input_type)
            self._log_audio_result(input_type, result)
            return result
        try:
            before_state = self._capture_real_demo_state("before")
            flow = self.runtime.process_audio(
                audio_path,
                deduplicate=input_type == "continuous_audio",
            )
            result = self._to_debug_result(input_type, flow)
            after_state = self._capture_real_demo_state("after")
            self._attach_real_demo_state(result, before_state, after_state)
            self._log_real_demo_command(result, before_state, after_state)
            self._log_audio_result(input_type, result)
            return result
        except Exception as exc:
            result = self._exception_debug(input_type, "audio", exc)
            self._log_audio_result(input_type, result)
            return result

    def start_continuous_listening(
        self,
        on_result: DebugCallback,
        on_event: EventCallback | None = None,
    ) -> bool:
        status = self.get_audio_status()
        if not status.available:
            if on_event:
                on_event("未监听")
            result = self.audio_dependency_result("continuous_audio")
            self.pipeline_logger.log_error("audio_dependency", result.message, command_id=result.command_id, mode="continuous_listening")
            on_result(result)
            return False
        asr_status = self.get_asr_status()
        if not asr_status.available:
            if on_event:
                on_event("未监听")
            result = self.asr_dependency_result("continuous_audio")
            self.pipeline_logger.log_error("asr_dependency", result.message, command_id=result.command_id, mode="continuous_listening")
            on_result(result)
            return False
        with self._audio_lock:
            if self._audio_state in {"one_shot_recording", "processing"}:
                on_result(
                    self._logged_busy_result(
                        "continuous_audio",
                        "One-shot voice is still processing. Please wait until it finishes.",
                    )
                )
                return False
            if self._audio_state == "continuous_listening":
                return False
            self._audio_state = "continuous_listening"
        self.pipeline_logger.start_continuous_listening(
            config={
                "listening": self.configs.app.get("listening", {}),
                "continuous_listening": self.configs.app.get("continuous_listening", {}),
                "command_detection": self.configs.app.get("command_detection", {}),
                "recognition": self.configs.app.get("recognition", {}),
                "semantic_engine": self.runtime.semantic_engine_config,
                "ui": self.configs.app.get("ui", {}),
            },
            audio_status=status.to_dict(),
            asr_status=asr_status.to_dict(),
        )
        if self._listener and self._listener.is_alive():
            return False
        self._listener = ContinuousListeningWorker(
            configs=self.configs,
            process_audio=self.process_audio_once,
            on_result=on_result,
            on_event=self._wrap_continuous_event(on_event),
            on_chunk=self.pipeline_logger.log_continuous_chunk,
        )
        self._listener.start()
        return True

    def start_one_shot_voice(
        self,
        on_result: DebugCallback,
        on_event: EventCallback | None = None,
    ) -> bool:
        status = self.get_audio_status()
        if not status.available:
            if on_event:
                on_event("空闲")
            result = self.audio_dependency_result("one_shot_audio")
            self.pipeline_logger.log_one_shot_result(result, "voice_chunk")
            on_result(result)
            return False
        asr_status = self.get_asr_status()
        if not asr_status.available:
            if on_event:
                on_event("空闲")
            result = self.asr_dependency_result("one_shot_audio")
            self.pipeline_logger.log_one_shot_result(result, "voice_chunk")
            on_result(result)
            return False
        with self._audio_lock:
            if self._audio_state == "continuous_listening":
                on_result(
                    self._logged_busy_result(
                        "one_shot_audio",
                        "Continuous listening is running. Stop it before using one-shot voice.",
                    )
                )
                return False
            if self._audio_state in {"one_shot_recording", "processing"}:
                on_result(
                    self._logged_busy_result(
                        "one_shot_audio",
                        "One-shot voice is still processing. Please wait until it finishes.",
                    )
                )
                return False
            self._audio_state = "one_shot_recording"
        self._one_shot = OneShotVoiceWorker(
            configs=self.configs,
            process_audio=self.process_audio_once,
            on_result=on_result,
            on_event=self._wrap_one_shot_event(on_event),
        )
        self._one_shot.start()
        return True

    def stop_continuous_listening(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener.join(timeout=8)
            self._listener = None
        with self._audio_lock:
            if self._audio_state == "continuous_listening":
                self._audio_state = "idle"
        self.pipeline_logger.end_continuous_listening()

    def submit_emergency_stop(self) -> PipelineDebugResult:
        return self.process_text_once("stop", input_type="emergency_stop")

    def get_audio_status(self, query_devices: bool = False) -> AudioDependencyStatus:
        self._last_audio_status = check_audio_dependencies(query_devices=query_devices)
        return self._last_audio_status

    def get_asr_status(self) -> AsrDependencyStatus:
        self._last_asr_status = self._check_asr_status()
        return self._last_asr_status

    def audio_dependency_result(self, input_type: str) -> PipelineDebugResult:
        status = self._last_audio_status
        if status.available:
            status = self.get_audio_status()
        return PipelineDebugResult(
            input_type=input_type,
            command_id=new_command_id(),
            accepted=False,
            stage="audio_dependency",
            message=status.user_message(),
            transcript_text="not executed",
            queue_result="not_started",
            error_stage="audio_dependency",
            error_message=status.user_message(),
        )

    def asr_dependency_result(self, input_type: str) -> PipelineDebugResult:
        status = self._last_asr_status
        if status.available:
            status = self.get_asr_status()
        return PipelineDebugResult(
            input_type=input_type,
            command_id=new_command_id(),
            accepted=False,
            stage="asr_dependency",
            message=status.user_message(),
            transcript_text="not executed",
            asr_diagnostics=status.to_dict(),
            queue_result="not_started",
            error_stage="asr_dependency",
            error_message=status.user_message(),
        )

    def audio_busy_result(self, input_type: str, message: str) -> PipelineDebugResult:
        return PipelineDebugResult(
            input_type=input_type,
            command_id=new_command_id(),
            accepted=False,
            stage="audio_busy",
            message=message,
            transcript_text="not executed",
            queue_result="not_started",
            error_stage="audio_busy",
            error_message=message,
        )

    def get_current_status(self) -> dict[str, object]:
        status = self.runtime.get_current_status()
        status["listening"] = bool(self._listener and self._listener.is_alive())
        status["audio_state"] = self._audio_state
        status["audio"] = self.get_audio_status(query_devices=False).to_dict()
        asr_status = self.get_asr_status()
        status["asr"] = asr_status.to_dict()
        qwen_config = self.configs.models.get("qwen", {})
        if isinstance(qwen_config, dict):
            qwen_dir = resolve_project_path(str(qwen_config.get("local_model_dir", "models/qwen")))
            status["qwen_model_dir"] = str(qwen_dir)
            status["qwen_mode"] = str(qwen_config.get("provider") or qwen_config.get("mode") or "rule_based")
        llm_status = self.runtime.llm_provider.status()
        status["semantic_engine"] = dict(self.runtime.semantic_engine_config)
        status["llm_provider"] = self.runtime.semantic_engine_config.get("llm_provider", "disabled")
        status["llm_enabled"] = self.runtime.semantic_engine_config.get("llm_enabled", False)
        status["llm_available"] = bool(llm_status.get("available"))
        status["llm_model_status"] = llm_status
        status["portable_status"] = "OK" if asr_status.is_project_venv else "WARN"
        status["logs"] = self.pipeline_logger.get_current_log_paths()
        status["settings"] = self.get_settings()
        status["real_demo"] = self.real_demo_settings()
        status["interface"] = str(self.configs.go2.get("network_interface") or "")
        return status

    def real_demo_settings(self) -> dict[str, object]:
        real_demo = self.configs.app.get("real_demo", {})
        if not isinstance(real_demo, dict):
            real_demo = {}
        allowed = self.configs.safety.get("allowed_real_actions") or real_demo.get("allowed_real_actions") or []
        return {
            "enabled": bool(real_demo.get("enabled", False)),
            "allowed_real_actions": list(allowed) if isinstance(allowed, list) else [],
            "continuous_requires_confirmation": bool(real_demo.get("continuous_requires_confirmation", True)),
            "continuous_confirm_token": str(real_demo.get("continuous_confirm_token") or "ENABLE_REAL_CONTINUOUS"),
            "dangerous_actions_disabled": bool(real_demo.get("dangerous_actions_disabled", True)),
            "interface": str(self.configs.go2.get("network_interface") or ""),
            "motion_limits": self.configs.go2.get("real_demo", {}),
        }

    def check_qwen_model_status(self) -> dict[str, object]:
        semantic = semantic_engine_config(self.configs.app, self.configs.models)
        return check_local_qwen_model(
            str(semantic.get("local_llm_model_dir", "models/qwen")),
            self.configs.config_dir.parent,
        ).to_dict()

    def get_settings(self) -> dict[str, object]:
        continuous = self.configs.app.get("continuous_listening", {})
        semantic = semantic_engine_config(self.configs.app, self.configs.models)
        return {
            "ui_language": str(self.configs.app.get("ui", {}).get("language", "en")),
            "recognition_preference": str(
                self.configs.app.get("recognition", {}).get("preference", "auto")
            ),
            "command_detection_mode": str(
                self.configs.app.get("command_detection", {}).get("mode", "strict")
            ),
            "deduplicate_enabled": bool(continuous.get("deduplicate_enabled", True)),
            "deduplicate_window_sec": float(continuous.get("deduplicate_window_sec", 3.0)),
            "same_intent_cooldown_sec": float(continuous.get("same_intent_cooldown_sec", 2.5)),
            "semantic_engine_mode": str(semantic.get("mode", "traditional")),
            "llm_enabled": bool(semantic.get("llm_enabled", False)),
            "llm_provider": str(semantic.get("llm_provider", "local_qwen")),
            "llm_fallback_min_confidence": float(semantic.get("llm_fallback_min_confidence", 0.60)),
            "local_llm_model_dir": str(semantic.get("local_llm_model_dir", "models/qwen")),
            "llm_timeout_seconds": float(semantic.get("llm_timeout_seconds", 5.0)),
            "llm_max_output_tokens": int(semantic.get("llm_max_output_tokens", 128)),
            "llm_temperature": float(semantic.get("llm_temperature", 0.0)),
            "llm_allow_remote_api": bool(semantic.get("llm_allow_remote_api", False)),
        }

    def save_user_settings(self, settings: dict[str, object]) -> None:
        path = self.configs.config_dir / "user_settings.yaml"
        existing = load_yaml(path) if path.exists() else {}
        updates = {
            "ui": {"language": settings.get("ui_language", "en")},
            "recognition": {"preference": settings.get("recognition_preference", "auto")},
            "command_detection": {"mode": settings.get("command_detection_mode", "strict")},
            "continuous_listening": {
                "deduplicate_enabled": bool(settings.get("deduplicate_enabled", True)),
                "deduplicate_window_sec": float(settings.get("deduplicate_window_sec", 3.0)),
                "same_intent_cooldown_sec": float(settings.get("same_intent_cooldown_sec", 2.5)),
            },
            "semantic_engine": {
                "mode": str(settings.get("semantic_engine_mode", "traditional")),
                "llm_enabled": bool(settings.get("llm_enabled", False)),
                "llm_provider": str(settings.get("llm_provider", "local_qwen")),
                "llm_fallback_min_confidence": float(settings.get("llm_fallback_min_confidence", 0.60)),
                "local_llm_model_dir": str(settings.get("local_llm_model_dir", "models/qwen")),
                "llm_timeout_seconds": float(settings.get("llm_timeout_seconds", 5.0)),
                "llm_max_output_tokens": int(settings.get("llm_max_output_tokens", 128)),
                "llm_temperature": float(settings.get("llm_temperature", 0.0)),
                "llm_allow_remote_api": bool(settings.get("llm_allow_remote_api", False)),
            },
        }
        merged = deep_merge(existing, updates)
        write_yaml(path, merged)
        self._merge_into(self.configs.app, updates)
        self._merge_into(self.configs.user_settings, updates)
        self.runtime.qwen.config["command_detection"] = self.configs.app.get("command_detection", {})
        self.runtime.qwen.config["recognition"] = self.configs.app.get("recognition", {})
        self.runtime.semantic_engine_config = semantic_engine_config(self.configs.app, self.configs.models)
        self.runtime.llm_decider.update_config(self.runtime.semantic_engine_config)
        self.runtime.llm_provider = build_llm_provider(
            self.runtime.semantic_engine_config,
            self.configs.config_dir.parent,
        )
        self.pipeline_logger.log_gui_event("settings saved", extra={"settings": self.get_settings()})

    def get_supported_commands(self) -> list[dict[str, object]]:
        commands = []
        action_intents = set()
        for action in self.runtime.catalog.action_specs():
            action_intents.add(action.intent)
            commands.append(
                {
                    "intent": action.intent,
                    "official_name": action.official_name,
                    "sdk_method": action.sdk_method,
                    "risk_level": action.risk_level,
                    "zh": action.aliases.get("zh", []),
                    "en": action.aliases.get("en", []),
                    "voice_enabled": action.voice_enabled,
                    "mock_enabled": action.mock_enabled,
                    "real_robot_enabled": action.real_robot_enabled,
                    "requires_duration": action.requires_duration,
                    "default_duration_sec": action.default_duration_sec,
                    "max_duration_sec": action.max_duration_sec,
                    "can_interrupt": action.can_interrupt,
                    "requires_robot_standing": action.requires_standing,
                    "description_en": action.description_en,
                    "description_zh": action.description_zh,
                    "reason": action.reason,
                }
            )
        for intent in self.runtime.catalog.intents():
            if intent in action_intents:
                continue
            spec = self.runtime.catalog.require(intent)
            commands.append(
                {
                    "intent": intent,
                    "official_name": spec.official_name,
                    "sdk_method": spec.sdk_method,
                    "risk_level": spec.risk_level,
                    "zh": (spec.aliases or {}).get("zh", []),
                    "en": (spec.aliases or {}).get("en", []),
                    "voice_enabled": spec.voice_enabled,
                    "mock_enabled": spec.mock_enabled,
                    "real_robot_enabled": spec.real_robot_enabled,
                    "requires_duration": spec.requires_duration,
                    "default_duration_sec": spec.default_duration_sec,
                    "max_duration_sec": spec.max_duration_sec,
                    "can_interrupt": spec.can_interrupt,
                    "requires_robot_standing": spec.requires_robot_standing,
                    "description_en": spec.description_en or spec.display_name,
                    "description_zh": spec.description_zh,
                    "reason": spec.reason,
                }
            )
        return commands

    def supported_commands_text(self, language: str = "en", risk_filter: str = "All") -> str:
        lines = []
        selected = str(risk_filter or "All").lower()
        for item in self.get_supported_commands():
            risk = str(item.get("risk_level", "safe")).lower()
            if selected != "all" and selected != risk:
                continue
            aliases = item.get("en" if language == "en" else "zh", [])
            other = item.get("zh" if language == "en" else "en", [])
            description = item.get("description_en" if language == "en" else "description_zh") or item.get(
                "description_en"
            )
            availability = (
                f"voice={'yes' if item.get('voice_enabled') else 'no'}, "
                f"mock={'yes' if item.get('mock_enabled') else 'no'}, "
                f"real={'yes' if item.get('real_robot_enabled') else 'no'}"
            )
            marker = " !!! " if risk == "dangerous" else ""
            lines.append(f"[{risk.upper()}]{marker}{item['intent']} -> {item.get('sdk_method') or item.get('official_name')}")
            lines.append(f"  aliases: {', '.join(str(x) for x in aliases) or '-'}")
            lines.append(f"  other: {', '.join(str(x) for x in other) or '-'}")
            lines.append(f"  availability: {availability}")
            if item.get("requires_robot_standing"):
                lines.append("  requires: standing")
            if item.get("requires_duration"):
                lines.append(
                    f"  duration: default {item.get('default_duration_sec')}s, max {item.get('max_duration_sec')}s"
                )
            if description:
                lines.append(f"  note: {description}")
            if item.get("reason"):
                lines.append(f"  reason: {item.get('reason')}")
            lines.append("")
        return "\n".join(lines)

    def _merge_into(self, target: dict[str, object], updates: dict[str, object]) -> None:
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                self._merge_into(target[key], value)  # type: ignore[index]
            else:
                target[key] = value

    def get_current_log_paths(self) -> dict[str, str]:
        return self.pipeline_logger.get_current_log_paths()

    def log_gui_event(self, message: str, status: str = "success") -> None:
        self.pipeline_logger.log_gui_event(message, status=status)

    def _log_audio_result(self, input_type: str, result: PipelineDebugResult) -> None:
        if input_type == "continuous_audio":
            self.pipeline_logger.log_continuous_result(result)
        else:
            self.pipeline_logger.log_one_shot_result(result, "voice_chunk")

    def _logged_busy_result(self, input_type: str, message: str) -> PipelineDebugResult:
        result = self.audio_busy_result(input_type, message)
        if input_type == "continuous_audio":
            self.pipeline_logger.log_error("audio_busy", message, command_id=result.command_id, mode="continuous_listening")
        else:
            self.pipeline_logger.log_one_shot_result(result, "gui_button")
        return result

    def _check_asr_status(self) -> AsrDependencyStatus:
        asr_config = self.configs.models.get("asr", {})
        whisper_config = self.configs.models.get("whisper", {})
        model_name = str(
            asr_config.get("model_size")
            or (whisper_config.get("name") if isinstance(whisper_config, dict) else "")
            or "base"
        )
        model_dir = resolve_whisper_model_dir(
            asr_config if isinstance(asr_config, dict) else {},
        )
        return check_asr_dependencies(model_name=model_name, model_dir=model_dir)

    def _wrap_one_shot_event(self, callback: EventCallback | None) -> EventCallback:
        display_map = {
            "recording": "正在录音",
            "recognizing": "正在识别",
            "processing": "正在处理",
            "idle": "空闲",
        }

        def wrapped(event: str) -> None:
            with self._audio_lock:
                if event == "recording":
                    self._audio_state = "one_shot_recording"
                elif event in {"recognizing", "processing"}:
                    self._audio_state = "processing"
                elif event == "idle":
                    self._audio_state = "idle"
            if callback:
                callback(display_map.get(event, event))

        return wrapped

    def _wrap_continuous_event(self, callback: EventCallback | None) -> EventCallback:
        display_map = {
            "processing": "正在处理",
            "listening": "正在监听",
            "idle": "未监听",
        }

        def wrapped(event: str) -> None:
            with self._audio_lock:
                if event == "idle":
                    self._audio_state = "idle"
                elif self._audio_state != "idle":
                    self._audio_state = "continuous_listening"
            if callback:
                callback(display_map.get(event, event))

        return wrapped

    def _to_debug_result(
        self,
        input_type: str,
        flow: CommandFlowResult,
    ) -> PipelineDebugResult:
        if flow.command_plan and not flow.command_plan.session_id:
            flow.command_plan.session_id = self.pipeline_logger.session_id
        adapter_result = None
        if flow.accepted:
            self.runtime.wait_until_idle(timeout_sec=15.0)
            adapter_result = (
                {"plan_results": flow.plan_results}
                if flow.plan_results and flow.command_plan and len(flow.command_plan.commands) > 1
                else self.runtime.get_adapter_result(flow.command_id)
            )
        elif flow.plan_results:
            adapter_result = {"plan_results": flow.plan_results}
        is_expected_skip = (
            bool(flow.semantic and not flow.semantic.is_command)
            or flow.stage in {"deduplicate", "confirmation", "semantic_debug"}
        )
        error_stage = None if flow.accepted or is_expected_skip else flow.stage
        error_message = None if flow.accepted or is_expected_skip else flow.message
        return PipelineDebugResult(
            input_type=input_type,
            command_id=flow.command_id,
            accepted=flow.accepted,
            stage=flow.stage,
            message=flow.message,
            transcript_text=flow.transcript.text if flow.transcript else "",
            asr_diagnostics=self._asr_diagnostics(flow),
            semantic_result=flow.semantic.to_dict() if flow.semantic else None,
            command_plan=flow.command_plan.to_dict() if flow.command_plan else None,
            robot_command=flow.command.to_dict() if flow.command else None,
            safety_decision=flow.safety.to_dict() if flow.safety else None,
            queue_result=flow.queue_status,
            adapter_result=adapter_result,
            error_stage=error_stage,
            error_message=error_message,
        )

    def _capture_real_demo_state(self, label: str) -> dict[str, object] | None:
        if not bool(self.real_demo_settings().get("enabled")):
            return None
        try:
            return {
                "label": label,
                "state": self.runtime.adapter.get_state().to_dict(),
                "error": "",
            }
        except Exception as exc:
            return {
                "label": label,
                "state": None,
                "error": f"{exc.__class__.__name__}: {exc}",
            }

    def _attach_real_demo_state(
        self,
        result: PipelineDebugResult,
        before_state: dict[str, object] | None,
        after_state: dict[str, object] | None,
    ) -> None:
        if before_state is None and after_state is None:
            return
        if not isinstance(result.adapter_result, dict):
            result.adapter_result = {}
        result.adapter_result["high_state_before"] = before_state
        result.adapter_result["high_state_after"] = after_state
        result.adapter_result["adapter"] = self.runtime.adapter.__class__.__name__

    def _log_real_demo_command(
        self,
        result: PipelineDebugResult,
        before_state: dict[str, object] | None,
        after_state: dict[str, object] | None,
    ) -> None:
        if not bool(self.real_demo_settings().get("enabled")):
            return
        path = self.pipeline_logger.paths.root / "commands.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": utc_now_iso(),
            "session_id": self.pipeline_logger.session_id,
            "command_id": result.command_id,
            "transcript": result.transcript_text,
            "intent": (result.robot_command or {}).get("intent") if result.robot_command else "",
            "command_plan": result.command_plan,
            "safety": result.safety_decision,
            "adapter": self.runtime.adapter.__class__.__name__,
            "sdk_method": self._sdk_method(result.adapter_result),
            "sdk_return": self._sdk_return(result.adapter_result),
            "adapter_result": result.adapter_result,
            "high_state_before": before_state,
            "high_state_after": after_state,
            "observed_note": "",
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def _sdk_method(self, adapter_result: object) -> str:
        raw = adapter_result.get("raw_response") if isinstance(adapter_result, dict) else None
        if isinstance(raw, dict) and raw.get("sdk_method"):
            return str(raw.get("sdk_method"))
        if isinstance(adapter_result, dict) and isinstance(adapter_result.get("plan_results"), list):
            for item in adapter_result.get("plan_results") or []:
                result = item.get("adapter_result") if isinstance(item, dict) else None
                method = self._sdk_method(result)
                if method:
                    return method
        return ""

    def _sdk_return(self, adapter_result: object) -> object:
        raw = adapter_result.get("raw_response") if isinstance(adapter_result, dict) else None
        if isinstance(raw, dict) and "code" in raw:
            return raw.get("code")
        if isinstance(adapter_result, dict) and isinstance(adapter_result.get("plan_results"), list):
            for item in adapter_result.get("plan_results") or []:
                result = item.get("adapter_result") if isinstance(item, dict) else None
                value = self._sdk_return(result)
                if value != "":
                    return value
        return ""

    def _asr_diagnostics(self, flow: CommandFlowResult) -> dict[str, object] | None:
        if flow.transcript is None:
            return None
        data = flow.transcript.to_dict()
        data.pop("raw_result", None)
        return data

    def _exception_debug(
        self,
        input_type: str,
        stage: str,
        exc: Exception,
    ) -> PipelineDebugResult:
        return PipelineDebugResult(
            input_type=input_type,
            command_id=new_command_id(),
            accepted=False,
            stage=stage,
            message=f"{exc.__class__.__name__}: {exc}",
            error_stage=stage,
            error_message=str(exc),
        )
