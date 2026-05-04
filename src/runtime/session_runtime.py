from __future__ import annotations

from pathlib import Path
import re
import threading
import time
from typing import Any

from src.asr.whisper_engine import WhisperEngine
from src.commands.command_catalog import CommandCatalog
from src.commands.go2_action_catalog import Go2ActionCatalog
from src.commands.normalizer import CommandNormalizer
from src.config import ConfigSet
from src.logging.event_logger import EventLogger
from src.models import (
    CommandPlan,
    CommandFlowResult,
    RobotCommand,
    SafetyDecision,
    SemanticResult,
    TranscriptResult,
    new_command_id,
    new_plan_id,
)
from src.nlu.asr_text_normalizer import AsrTextNormalizer, AsrTextNormalization
from src.nlu.fuzzy_command_resolver import FuzzyCommandResolver
from src.nlu.non_command_filter import NonCommandFilter
from src.nlu.qwen_engine import QwenEngine
from src.nlu.sequence_command_parser import SequenceCommandParser
from src.robot.go2_adapter import Go2Adapter
from src.robot.mock_adapter import MockAdapter
from src.runtime.command_queue import CommandQueue
from src.safety.safety_controller import SafetyController


class SessionRuntime:
    def __init__(self, configs: ConfigSet):
        self.configs = configs
        self.logger = EventLogger(configs.log_dir / "events")
        self.action_catalog = Go2ActionCatalog(configs.go2_actions)
        self.catalog = CommandCatalog(configs.commands, configs.go2_actions)
        self.normalizer = CommandNormalizer(self.catalog)
        qwen_config = dict(configs.models.get("qwen", {}))
        qwen_config["command_detection"] = configs.app.get("command_detection", {})
        qwen_config["recognition"] = configs.app.get("recognition", {})
        qwen_config["go2_action_catalog"] = configs.go2_actions
        self.qwen = QwenEngine(qwen_config)
        asr_config = dict(configs.models.get("asr", {}))
        whisper_config = configs.models.get("whisper", {})
        if isinstance(whisper_config, dict):
            self._merge_whisper_config(asr_config, whisper_config)
        self.whisper = WhisperEngine(asr_config)
        self.adapter = self._build_adapter()
        self.safety = SafetyController(
            configs.safety,
            self.catalog,
            robot_mode=configs.robot_mode,
            enable_real_robot=configs.enable_real_robot,
        )
        self.queue = CommandQueue(
            self.adapter,
            self.catalog,
            self.logger,
            config=configs.app.get("command_queue", {}),
        )
        plan_config = configs.app.get("command_plan", {})
        extra_en_words, extra_zh_words = self.action_catalog.sequence_keywords()
        self.sequence_parser = SequenceCommandParser(
            max_commands=int(plan_config.get("max_commands_per_utterance", 3)),
            extra_en_words=extra_en_words,
            extra_zh_words=extra_zh_words,
        )
        self.asr_text_normalizer = AsrTextNormalizer()
        self.non_command_filter = NonCommandFilter()
        self.fuzzy_resolver = FuzzyCommandResolver(configs.app.get("fuzzy_command", {}))
        self._recent_command_memory: dict[str, tuple[float, str]] = {}
        self._recent_plan_memory: dict[str, tuple[float, str]] = {}
        self._dedupe_lock = threading.Lock()

    @classmethod
    def from_config_dir(cls, config_dir: str | Path | None = None) -> "SessionRuntime":
        return cls(ConfigSet.load(config_dir))

    def _merge_whisper_config(
        self,
        asr_config: dict[str, Any],
        whisper_config: dict[str, Any],
    ) -> None:
        aliases = {
            "download_root": "download_root",
            "model_dir": "download_root",
            "allow_download": "allow_download",
            "name": "model_size",
            "model_name": "model_size",
            "language": "language",
            "task": "task",
            "fp16": "fp16",
            "temperature": "temperature",
            "condition_on_previous_text": "condition_on_previous_text",
            "initial_prompt": "initial_prompt",
        }
        for source_key, target_key in aliases.items():
            if source_key in whisper_config and target_key not in asr_config:
                asr_config[target_key] = whisper_config[source_key]

    def start(self) -> None:
        if self.configs.robot_mode == "go2" and self.configs.enable_real_robot:
            from src.deployment.env_checker import EnvChecker

            report = EnvChecker(self.configs).check_all()
            failed = [item for item in report if item.status == "FAIL"]
            if failed:
                details = "; ".join(f"{item.name}: {item.message}" for item in failed)
                raise RuntimeError(f"Go2 preflight failed: {details}")
        self.adapter.connect()
        self.queue.start()
        self.logger.log(
            "session",
            "runtime_started",
            robot_mode=self.configs.robot_mode,
            enable_real_robot=self.configs.enable_real_robot,
        )

    def shutdown(self) -> None:
        self.queue.shutdown()
        self.adapter.disconnect()
        self.logger.log("session", "runtime_shutdown")
        self.logger.close()

    def wait_until_idle(self, timeout_sec: float = 10.0) -> bool:
        return self.queue.wait_until_idle(timeout_sec)

    def get_current_status(self) -> dict[str, object]:
        return {
            "robot_mode": self.configs.robot_mode,
            "enable_real_robot": self.configs.enable_real_robot,
            "adapter": self.adapter.__class__.__name__,
            "asr_provider": self.configs.models.get("asr", {}).get("provider", "whisper"),
            "qwen_provider": self.configs.models.get("qwen", {}).get("provider", "rule_based"),
            "queue_current": self.queue.current_command_id(),
            "queue_pending": self.queue.pending_count(),
        }

    def get_adapter_result(self, command_id: str) -> dict[str, object] | None:
        result = self.queue.results.get(command_id)
        return result.to_dict() if result else None

    def process_audio(
        self,
        audio_path: str | Path,
        deduplicate: bool = False,
    ) -> CommandFlowResult:
        command_id = new_command_id()
        transcript = self.whisper.transcribe(audio_path)
        self.logger.log(
            "asr",
            "transcribe",
            command_id=command_id,
            audio_path=str(audio_path),
            transcript=transcript.to_dict(),
        )
        threshold = float(self.configs.models.get("asr", {}).get("no_speech_threshold", 0.6))
        if not transcript.text:
            message = transcript.error_message or "ASR did not recognize any text."
            return CommandFlowResult(
                command_id,
                False,
                "asr",
                message,
                transcript=transcript,
            )
        if transcript.no_speech_prob > threshold:
            self.logger.log(
                "asr",
                "high_no_speech_prob_with_text",
                command_id=command_id,
                no_speech_prob=transcript.no_speech_prob,
                threshold=threshold,
                text=transcript.text,
            )
        return self.process_text(
            transcript.text,
            command_id=command_id,
            transcript=transcript,
            deduplicate=deduplicate,
        )

    def process_text(
        self,
        text: str,
        command_id: str | None = None,
        transcript: TranscriptResult | None = None,
        deduplicate: bool = False,
    ) -> CommandFlowResult:
        cid = command_id or new_command_id()
        transcript = transcript or TranscriptResult(text=text, no_speech_prob=0.0)
        try:
            semantic_items, parse_meta = self._parse_semantic_items(text)
            if not semantic_items:
                semantic = parse_meta.get("semantic_result")
                if not isinstance(semantic, SemanticResult):
                    semantic = self.qwen.parse_command(text)
                self.logger.log(
                    "nlu",
                    "parse_command",
                    command_id=cid,
                    source_text=text,
                    semantic=semantic.to_dict(),
                )
                return CommandFlowResult(
                    cid,
                    False,
                    "semantic",
                    semantic.reason or "not a robot command",
                    transcript=transcript,
                    semantic=semantic,
                    queue_status="not_submitted",
                )
            semantic = semantic_items[0][1]
            self.logger.log(
                "nlu",
                "parse_command_plan",
                command_id=cid,
                source_text=text,
                semantic_items=[
                    {"source_span": span, "semantic": item.to_dict()}
                    for span, item in semantic_items
                ],
                parse_meta=parse_meta,
            )
            commands = self._normalize_plan_commands(semantic_items, text, cid)
            command = commands[0]
            plan = self._build_command_plan(text, semantic_items, commands, parse_meta)
            self.logger.log(
                "session",
                "normalized_command_plan",
                command_id=cid,
                plan_id=plan.plan_id,
                command_plan=plan.to_dict(),
            )

            if plan.needs_confirmation:
                return CommandFlowResult(
                    cid,
                    False,
                    "confirmation",
                    plan.reason,
                    transcript=transcript,
                    semantic=semantic,
                    command=command,
                    command_plan=plan,
                    queue_status="not_submitted",
                )

            if deduplicate and self._is_duplicate_plan(plan, text):
                self.logger.log(
                    "session",
                    "duplicate_continuous_plan_skipped",
                    command_id=cid,
                    plan_id=plan.plan_id,
                    intent_sequence=plan.intent_sequence,
                    dedup_signature=plan.dedup_signature,
                    source_text=text,
                )
                return CommandFlowResult(
                    cid,
                    False,
                    "deduplicate",
                    "duplicate continuous command plan skipped",
                    transcript=transcript,
                    semantic=semantic,
                    command=command,
                    command_plan=plan,
                    queue_status="deduplicated",
                )

            result = self._execute_plan(plan, semantic_items, transcript, cid, deduplicate)
            if result.command_plan is None:
                result.command_plan = plan
            return result
        except Exception as exc:
            self.logger.exception("session", "process_text_failed", exc, command_id=cid, text=text)
            return CommandFlowResult(
                cid,
                False,
                "exception",
                f"{exc.__class__.__name__}: {exc}",
                transcript=transcript,
                safety=SafetyDecision(False, "exception"),
            )

    def _parse_semantic_items(self, text: str) -> tuple[list[tuple[str, SemanticResult]], dict[str, object]]:
        plan_config = self.configs.app.get("command_plan", {})
        enabled = bool(plan_config.get("enabled", True))
        normalization = self.asr_text_normalizer.normalize(text, self._command_detection_mode())
        parse_text = normalization.normalized_text
        base_meta: dict[str, object] = {"asr_text_normalization": normalization.to_dict()}
        if normalization.reject_reason:
            semantic = self._semantic_from_normalization_rejection(normalization)
            return [], {
                **base_meta,
                "plan_type": "none",
                "semantic_result": semantic,
                "ambiguous_rejected": True,
            }
        non_command = self.non_command_filter.classify(parse_text)
        if self._command_detection_mode() == "strict" and non_command.is_non_command:
            semantic = self._semantic_from_non_command_filter(parse_text, non_command.reason)
            return [], {
                **base_meta,
                "plan_type": "none",
                "semantic_result": semantic,
                "non_command_rejected": True,
                "non_command_reason": non_command.reason,
            }
        if not enabled:
            semantic = self._parse_single_span(parse_text, parse_text)
            self._apply_normalization_to_semantic(semantic, normalization)
            return ([(text, semantic)] if semantic.is_command else []), {"plan_type": "single", "enabled": False}

        split = self.sequence_parser.split(parse_text)
        spans = split.spans or [parse_text]
        items: list[tuple[str, SemanticResult]] = []
        for span in spans:
            semantic = self._parse_single_span(span, parse_text)
            self._apply_normalization_to_semantic(semantic, normalization)
            if semantic.is_command:
                items.append((span, semantic))
        if not items and len(spans) != 1:
            semantic = self._parse_single_span(parse_text, parse_text)
            self._apply_normalization_to_semantic(semantic, normalization)
            if semantic.is_command:
                items.append((parse_text, semantic))
        if not items:
            return [], {
                **base_meta,
                "plan_type": "none",
                "truncated": split.truncated,
                "truncated_count": split.truncated_count,
                "connectors_found": split.connectors_found,
            }

        first_stop_index = next((index for index, (_, item) in enumerate(items) if item.intent == "stop"), None)
        stop_trimmed_count = 0
        if first_stop_index is not None:
            stop_trimmed_count = max(0, len(items) - first_stop_index - 1)
            items = items[: first_stop_index + 1]
        return items, {
            **base_meta,
            "plan_type": "sequence" if len(items) > 1 else "single",
            "truncated": split.truncated or stop_trimmed_count > 0,
            "truncated_count": split.truncated_count + stop_trimmed_count,
            "connectors_found": split.connectors_found,
            "stop_trimmed_count": stop_trimmed_count,
        }

    def _semantic_from_normalization_rejection(self, normalization: AsrTextNormalization) -> SemanticResult:
        return SemanticResult(
            is_command=False,
            intent="none",
            source_language="en" if re.search(r"[A-Za-z]", normalization.original_text) else "unknown",
            confidence=float(normalization.confidence or 0.0),
            need_clarification=normalization.needs_confirmation,
            dangerous=False,
            reason=normalization.reject_reason,
            raw_result={
                "provider": "asr_text_normalizer",
                "asr_text_normalization": normalization.to_dict(),
            },
        )

    def _semantic_from_non_command_filter(self, text: str, reason: str) -> SemanticResult:
        return SemanticResult(
            is_command=False,
            intent="none",
            source_language="en" if re.search(r"[A-Za-z]", text) else "zh" if re.search(r"[\u4e00-\u9fff]", text) else "unknown",
            confidence=0.95,
            need_clarification=False,
            dangerous=False,
            reason=reason,
            raw_result={
                "provider": "non_command_filter",
                "text": text,
                "non_command_reason": reason,
            },
        )

    def _apply_normalization_to_semantic(
        self,
        semantic: SemanticResult,
        normalization: AsrTextNormalization,
    ) -> None:
        if not normalization.ambiguity_flags:
            return
        semantic.raw_result["asr_text_normalization"] = normalization.to_dict()
        if normalization.inferred_intent:
            semantic.raw_result["inferred"] = True
            semantic.raw_result["inference_reason"] = ",".join(normalization.ambiguity_flags)
        if normalization.confidence is not None:
            semantic.confidence = min(semantic.confidence, float(normalization.confidence))
        if normalization.needs_confirmation:
            semantic.need_clarification = True
        semantic.reason = f"{semantic.reason}; ASR ambiguity: {', '.join(normalization.ambiguity_flags)}"

    def _parse_single_span(self, span: str, full_text: str) -> SemanticResult:
        fuzzy_source = full_text if self._looks_like_relative_fuzzy(full_text) else span
        fuzzy = self.fuzzy_resolver.resolve(fuzzy_source)
        if fuzzy is not None:
            return fuzzy
        return self.qwen.parse_command(span)

    def _looks_like_relative_fuzzy(self, text: str) -> bool:
        lowered = text.lower()
        return (
            "come here" in lowered
            or "过来" in text
            or "来这里" in text
        ) and (
            "your left" in lowered
            or "your right" in lowered
            or "你左边" in text
            or "你右边" in text
        )

    def _normalize_plan_commands(
        self,
        semantic_items: list[tuple[str, SemanticResult]],
        source_text: str,
        first_command_id: str,
    ) -> list[RobotCommand]:
        total = len(semantic_items)
        commands: list[RobotCommand] = []
        for index, (span, semantic) in enumerate(semantic_items, start=1):
            command = self.normalizer.normalize(
                semantic,
                source_text,
                command_id=first_command_id if index == 1 else new_command_id(),
            )
            inferred = bool(semantic.raw_result.get("inferred"))
            inference_reason = str(semantic.raw_result.get("inference_reason") or "")
            command.sequence_index = index
            command.sequence_total = total
            command.source_span = span
            command.inferred = inferred
            command.inference_reason = inference_reason
            command.metadata.update(
                {
                    "source_span": span,
                    "inferred": inferred,
                    "inference_reason": inference_reason,
                    "semantic_confidence": semantic.confidence,
                }
            )
            commands.append(command)
        return commands

    def _build_command_plan(
        self,
        source_text: str,
        semantic_items: list[tuple[str, SemanticResult]],
        commands: list[RobotCommand],
        parse_meta: dict[str, object],
    ) -> CommandPlan:
        confidences = [semantic.confidence for _, semantic in semantic_items]
        fuzzy_config = self.configs.app.get("fuzzy_command", {})
        min_fuzzy_confidence = float(fuzzy_config.get("min_confidence_to_execute", 0.65))
        has_low_fuzzy = any(
            bool(semantic.raw_result.get("inferred")) and semantic.confidence < min_fuzzy_confidence
            for _, semantic in semantic_items
        )
        command_detection = self.configs.app.get("command_detection", {})
        mode = self._command_detection_mode()
        min_confidence = float(
            command_detection.get(
                "strict_min_confidence_to_execute"
                if mode == "strict"
                else "relaxed_min_confidence_to_execute",
                0.70 if mode == "strict" else 0.50,
            )
        )
        has_low_confidence = any(
            semantic.intent != "stop"
            and not semantic.dangerous
            and semantic.confidence < min_confidence
            for _, semantic in semantic_items
        )
        has_non_executable = any(
            getattr(semantic, "rejected_by_nlu", False) or getattr(semantic, "executable", True) is False
            for _, semantic in semantic_items
        )
        needs_confirmation = (
            any(semantic.need_clarification for _, semantic in semantic_items)
            or has_low_fuzzy
            or has_low_confidence
            or has_non_executable
        )
        unsupported = [
            command.intent
            for command, (_, semantic) in zip(commands, semantic_items)
            if self.catalog.get(command.intent) is None and not semantic.dangerous
        ]
        if unsupported:
            needs_confirmation = True
        reasons = [semantic.reason for _, semantic in semantic_items if semantic.reason]
        if has_low_confidence:
            reasons.append(
                f"semantic confidence below {min_confidence:.2f} for {mode} command detection"
            )
        if unsupported:
            reasons.append(f"Unsupported or unresolved intent(s): {', '.join(unsupported)}")
        if has_non_executable:
            reasons.append("One or more catalog actions are not executable from a voice command")
        plan = CommandPlan(
            plan_id=new_plan_id(),
            session_id="",
            source_text=source_text,
            source_language=self._merge_source_languages([semantic.source_language for _, semantic in semantic_items]),
            parse_mode=str(parse_meta.get("plan_type") or "single"),
            commands=commands,
            confidence=min(confidences) if confidences else 0.0,
            needs_confirmation=needs_confirmation,
            reason="; ".join(reasons) if reasons else "Command plan parsed.",
            plan_type=str(parse_meta.get("plan_type") or "single"),
            truncated=bool(parse_meta.get("truncated")),
            truncated_count=int(parse_meta.get("truncated_count") or 0),
            fuzzy_detected=any(bool(semantic.raw_result.get("inferred")) for _, semantic in semantic_items),
            metadata=parse_meta,
        )
        plan.dedup_signature = self._plan_signature(plan)
        return plan

    def _execute_plan(
        self,
        plan: CommandPlan,
        semantic_items: list[tuple[str, SemanticResult]],
        transcript: TranscriptResult,
        cid: str,
        deduplicate: bool,
    ) -> CommandFlowResult:
        plan_results: list[dict[str, Any]] = []
        first_semantic = semantic_items[0][1]
        first_command = plan.commands[0]
        first_decision: SafetyDecision | None = None
        final_queue_status = "not_submitted"
        plan_config = self.configs.app.get("command_plan", {})
        stop_plan_on_rejection = bool(plan_config.get("stop_plan_on_rejection", True))
        command_gap_sec = float(plan_config.get("command_gap_sec", 0.3))

        for index, command in enumerate(plan.commands):
            semantic = semantic_items[index][1]
            decision = self.safety.check(semantic, command, self.adapter.get_state())
            if first_decision is None:
                first_decision = decision
            self.logger.log(
                "safety",
                "plan_command_safety_decision",
                command_id=command.command_id,
                plan_id=plan.plan_id,
                sequence_index=command.sequence_index,
                decision=decision.to_dict(),
            )
            plan_results.append(
                {
                    "command_id": command.command_id,
                    "intent": command.intent,
                    "sequence_index": command.sequence_index,
                    "safety": decision.to_dict(),
                    "queue_status": "not_submitted",
                }
            )
            if not decision.allowed:
                if stop_plan_on_rejection:
                    final_queue_status = "rejected"
                return CommandFlowResult(
                    cid,
                    False,
                    "safety",
                    decision.reason,
                    transcript=transcript,
                    semantic=first_semantic,
                    command=first_command,
                    safety=decision,
                    queue_status=final_queue_status,
                    command_plan=plan,
                    plan_results=plan_results,
                )

            queue_status = self.queue.submit(decision.normalized_command or command)
            final_queue_status = queue_status
            plan_results[-1]["queue_status"] = queue_status
            self.wait_until_idle(timeout_sec=15.0)
            adapter_result = self.get_adapter_result(command.command_id)
            if adapter_result:
                plan_results[-1]["adapter_result"] = adapter_result
            if queue_status.startswith("rejected"):
                return CommandFlowResult(
                    cid,
                    False,
                    "queue",
                    queue_status,
                    transcript=transcript,
                    semantic=first_semantic,
                    command=first_command,
                    safety=decision,
                    queue_status=queue_status,
                    command_plan=plan,
                    plan_results=plan_results,
                )
            if command.intent == "stop":
                if len(plan.commands) > 1:
                    final_queue_status = "plan_stopped"
                break
            if index < len(plan.commands) - 1 and command_gap_sec > 0:
                time.sleep(command_gap_sec)

        if deduplicate:
            self._remember_plan(plan, plan.source_text)
            self._remember_command(first_command.intent, plan.source_text)
        message = (
            "plan executed: " + " -> ".join(plan.intent_sequence)
            if len(plan.commands) > 1
            else final_queue_status
        )
        return CommandFlowResult(
            cid,
            True,
            "queue",
            message,
            transcript=transcript,
            semantic=first_semantic,
            command=first_command,
            safety=first_decision,
            queue_status="plan_completed" if len(plan.commands) > 1 else final_queue_status,
            command_plan=plan,
            plan_results=plan_results,
        )

    def _merge_source_languages(self, languages: list[str]) -> str:
        clean = {language for language in languages if language and language != "unknown"}
        if not clean:
            return "unknown"
        if len(clean) == 1:
            return next(iter(clean))
        return "mixed"

    def _plan_signature(self, plan: CommandPlan) -> str:
        return "->".join(plan.intent_sequence)

    def _command_detection_mode(self) -> str:
        return str(
            self.configs.app.get("command_detection", {}).get("mode", "strict")
        ).lower()

    def _is_duplicate_plan(self, plan: CommandPlan, source_text: str) -> bool:
        if "stop" in plan.intent_sequence:
            return False
        config = self.configs.app.get("continuous_listening", {})
        if not bool(config.get("deduplicate_plan_enabled", config.get("deduplicate_enabled", True))):
            return False
        deduplicate_sec = float(
            config.get("deduplicate_plan_window_sec")
            or config.get("deduplicate_window_sec")
            or self.configs.app.get("listening", {}).get("deduplicate_sec", 3.0)
        )
        now = time.monotonic()
        signature = plan.dedup_signature or self._plan_signature(plan)
        with self._dedupe_lock:
            last = self._recent_plan_memory.get(signature)
            if not last:
                return False
            last_time, _last_text = last
            return now - last_time <= deduplicate_sec

    def _remember_plan(self, plan: CommandPlan, source_text: str) -> None:
        if "stop" in plan.intent_sequence:
            return
        with self._dedupe_lock:
            self._recent_plan_memory[plan.dedup_signature or self._plan_signature(plan)] = (
                time.monotonic(),
                self._normalize_for_dedupe(source_text),
            )

    def _is_duplicate_command(self, intent: str, source_text: str) -> bool:
        if intent == "stop":
            return False
        config = self.configs.app.get("continuous_listening", {})
        if not bool(config.get("deduplicate_enabled", True)):
            return False
        deduplicate_sec = float(
            config.get("same_intent_cooldown_sec")
            or config.get("deduplicate_window_sec")
            or self.configs.app.get("listening", {}).get("deduplicate_sec", 3.0)
        )
        normalized_text = self._normalize_for_dedupe(source_text)
        now = time.monotonic()
        with self._dedupe_lock:
            last = self._recent_command_memory.get(intent)
            if not last:
                return False
            last_time, last_text = last
            if now - last_time > deduplicate_sec:
                return False
            return True

    def _remember_command(self, intent: str, source_text: str) -> None:
        if intent == "stop":
            return
        with self._dedupe_lock:
            self._recent_command_memory[intent] = (
                time.monotonic(),
                self._normalize_for_dedupe(source_text),
            )

    def _normalize_for_dedupe(self, text: str) -> str:
        return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", text.lower())

    def _build_adapter(self):
        if self.configs.robot_mode == "go2" and self.configs.enable_real_robot:
            return Go2Adapter(self.configs.go2)
        return MockAdapter(self.catalog)
