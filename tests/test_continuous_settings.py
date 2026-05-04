from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.config import ConfigSet
from src.logging.pipeline_logger import PipelineLogger
from src.models import PipelineDebugResult
from src.nlu.qwen_engine import QwenEngine
from src.runtime.session_runtime import SessionRuntime


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CommandDetectionModeTest(unittest.TestCase):
    def test_strict_mode_ignores_example_sentence(self) -> None:
        engine = QwenEngine(
            {
                "provider": "rule_based",
                "command_detection": {"mode": "strict"},
            }
        )
        result = engine.parse_command("I said sit down in the example.")
        self.assertFalse(result.is_command)
        self.assertEqual(result.intent, "none")

    def test_strict_mode_accepts_clear_prefixed_command(self) -> None:
        engine = QwenEngine(
            {
                "provider": "rule_based",
                "command_detection": {"mode": "strict"},
            }
        )
        result = engine.parse_command("Go2, sit down.")
        self.assertTrue(result.is_command)
        self.assertEqual(result.intent, "sit_down")

    def test_relaxed_mode_accepts_direct_keyword_sentence(self) -> None:
        engine = QwenEngine(
            {
                "provider": "rule_based",
                "command_detection": {"mode": "relaxed"},
            }
        )
        result = engine.parse_command("I said sit down in the example.")
        self.assertTrue(result.is_command)
        self.assertEqual(result.intent, "sit_down")

    def test_stop_works_in_strict_mode(self) -> None:
        engine = QwenEngine(
            {
                "provider": "rule_based",
                "command_detection": {"mode": "strict"},
            }
        )
        result = engine.parse_command("stop")
        self.assertTrue(result.is_command)
        self.assertEqual(result.intent, "stop")


class ContinuousDeduplicationTest(unittest.TestCase):
    def test_same_intent_is_deduplicated_during_cooldown(self) -> None:
        configs = ConfigSet.load(PROJECT_ROOT / "configs")
        configs.app["robot_mode"] = "mock"
        configs.app["enable_real_robot"] = False
        configs.go2["robot_mode"] = "mock"
        configs.go2["enable_real_robot"] = False
        configs.app["continuous_listening"]["deduplicate_enabled"] = True
        configs.app["continuous_listening"]["same_intent_cooldown_sec"] = 10.0
        runtime = SessionRuntime(configs)
        runtime.start()
        try:
            first = runtime.process_text("Go2, stand up.", deduplicate=True)
            self.assertTrue(first.accepted, first.message)
            second = runtime.process_text("Please stand up.", deduplicate=True)
            self.assertFalse(second.accepted)
            self.assertEqual(second.stage, "deduplicate")
            self.assertEqual(second.queue_status, "deduplicated")
        finally:
            runtime.shutdown()

    def test_stop_is_not_deduplicated(self) -> None:
        configs = ConfigSet.load(PROJECT_ROOT / "configs")
        runtime = SessionRuntime(configs)
        runtime.start()
        try:
            first = runtime.process_text("stop", deduplicate=True)
            second = runtime.process_text("stop", deduplicate=True)
            self.assertTrue(first.accepted)
            self.assertTrue(second.accepted)
            self.assertEqual(second.queue_status, "emergency_queued")
        finally:
            runtime.shutdown()


class ContinuousSummaryCountTest(unittest.TestCase):
    def test_safety_rejection_is_not_counted_as_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logger = PipelineLogger(root, project_root=root)
            run = logger.start_continuous_listening()
            logger.log_continuous_chunk({"chunk_status": "command_detected"})
            logger.log_continuous_result(
                PipelineDebugResult(
                    input_type="continuous_audio",
                    command_id="cmd_safety",
                    accepted=False,
                    stage="safety",
                    message="robot must be standing before this action",
                    semantic_result={"is_command": True, "intent": "move_forward"},
                    safety_decision={"allowed": False, "reason": "robot must be standing before this action"},
                    queue_result="rejected",
                    error_stage="safety",
                    error_message="robot must be standing before this action",
                )
            )
            logger.end_continuous_listening()
            summary = run.summary_path.read_text(encoding="utf-8")
            self.assertIn("Safety rejected: 1", summary)
            self.assertIn("Error count: 0", summary)


if __name__ == "__main__":
    unittest.main()
