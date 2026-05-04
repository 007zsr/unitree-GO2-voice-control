from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.config import ConfigSet
from src.logging.pipeline_logger import PipelineLogger
from src.models import PipelineDebugResult
from src.nlu.qwen_engine import QwenEngine
from src.runtime.session_runtime import SessionRuntime


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class StrictNluPolicyTest(unittest.TestCase):
    def test_strict_rejects_single_direction_words(self) -> None:
        engine = QwenEngine({"provider": "rule_based", "command_detection": {"mode": "strict"}})
        for text in ["Right.", "Left.", "Forward.", "Back."]:
            result = engine.parse_command(text)
            self.assertFalse(result.is_command, text)
            self.assertEqual(result.reason, "single_direction_word_rejected_in_strict_mode")

    def test_strict_allows_explicit_direction_commands(self) -> None:
        engine = QwenEngine({"provider": "rule_based", "command_detection": {"mode": "strict"}})
        cases = {
            "Turn right.": "turn_right",
            "Please turn left.": "turn_left",
            "Go2, right.": "turn_right",
        }
        for text, intent in cases.items():
            result = engine.parse_command(text)
            self.assertTrue(result.is_command, text)
            self.assertEqual(result.intent, intent)

    def test_stop_remains_single_word_emergency(self) -> None:
        engine = QwenEngine({"provider": "rule_based", "command_detection": {"mode": "strict"}})
        result = engine.parse_command("Stop.")
        self.assertTrue(result.is_command)
        self.assertEqual(result.intent, "stop")

    def test_relaxed_can_match_single_direction_word(self) -> None:
        engine = QwenEngine({"provider": "rule_based", "command_detection": {"mode": "relaxed"}})
        result = engine.parse_command("Right.")
        self.assertTrue(result.is_command)
        self.assertEqual(result.intent, "turn_right")
        self.assertTrue(result.raw_result.get("matched_in_relaxed_mode"))


class AsrAmbiguityPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        configs = ConfigSet.load(PROJECT_ROOT / "configs")
        configs.app["robot_mode"] = "mock"
        configs.app["enable_real_robot"] = False
        configs.go2["robot_mode"] = "mock"
        configs.go2["enable_real_robot"] = False
        configs.app.setdefault("command_detection", {})["mode"] = "strict"
        self.runtime = SessionRuntime(configs)
        self.runtime.start()

    def tearDown(self) -> None:
        self.runtime.shutdown()

    def test_turn_life_is_rejected_as_ambiguous_in_strict_mode(self) -> None:
        result = self.runtime.process_text("turn life")
        self.assertFalse(result.accepted)
        self.assertEqual(result.stage, "semantic")
        self.assertEqual(result.semantic.reason, "ambiguous_asr_turn_left")

    def test_turn_off_turn_right_is_rejected_as_ambiguous(self) -> None:
        result = self.runtime.process_text("Turn off the turn right.")
        self.assertFalse(result.accepted)
        self.assertEqual(result.stage, "semantic")
        self.assertEqual(result.semantic.reason, "ambiguous_turn_off_phrase")


class SafetyLogNamingTest(unittest.TestCase):
    def test_safety_rejection_does_not_write_error_stage_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logger = PipelineLogger(root, project_root=root)
            result = PipelineDebugResult(
                input_type="continuous_audio",
                command_id="cmd_safety",
                accepted=False,
                stage="safety",
                message="robot must be standing before this action",
                semantic_result={"is_command": True, "intent": "turn_right"},
                safety_decision={
                    "allowed": False,
                    "reason": "robot must be standing before this action",
                },
                queue_result="rejected",
                error_stage="safety",
                error_message="robot must be standing before this action",
            )
            run = logger.start_continuous_listening()
            logger.log_continuous_chunk({"chunk_status": "safety_rejected"})
            logger.log_continuous_result(result)
            logger.end_continuous_listening()

            records = [
                json.loads(line)
                for line in run.commands_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(any(record["stage"] == "safety_rejected" for record in records))
            self.assertFalse(any(record["stage"] == "error" for record in records))
            summary = run.summary_path.read_text(encoding="utf-8")
            self.assertIn("Safety rejected: 1", summary)
            self.assertIn("System errors: 0", summary)


if __name__ == "__main__":
    unittest.main()
