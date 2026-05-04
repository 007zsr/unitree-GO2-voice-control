from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ConfigSet
from src.nlu.qwen_engine import QwenEngine
from src.runtime.session_runtime import SessionRuntime


class CommandFlowTest(unittest.TestCase):
    def setUp(self) -> None:
        configs = ConfigSet.load(PROJECT_ROOT / "configs")
        configs.app["robot_mode"] = "mock"
        configs.app["enable_real_robot"] = False
        configs.go2["robot_mode"] = "mock"
        configs.go2["enable_real_robot"] = False
        self.runtime = SessionRuntime(configs)
        self.runtime.start()

    def tearDown(self) -> None:
        self.runtime.shutdown()

    def test_forward_one_second_is_accepted_in_mock(self) -> None:
        result = self.runtime.process_text("向前走一秒")
        self.assertTrue(result.accepted, result.message)
        self.assertEqual(result.semantic.intent, "move_forward")
        self.assertEqual(result.command.duration_sec, 1.0)
        self.assertTrue(self.runtime.wait_until_idle(timeout_sec=3))
        self.assertEqual(self.runtime.queue.status[result.command_id], "completed")

    def test_english_forward_one_second_is_accepted_in_mock(self) -> None:
        result = self.runtime.process_text("move forward for one second")
        self.assertTrue(result.accepted, result.message)
        self.assertEqual(result.semantic.intent, "move_forward")
        self.assertEqual(result.semantic.source_language, "en")
        self.assertEqual(result.command.duration_sec, 1.0)
        self.assertTrue(self.runtime.wait_until_idle(timeout_sec=3))

    def test_stop_is_emergency_queued(self) -> None:
        result = self.runtime.process_text("停下")
        self.assertTrue(result.accepted, result.message)
        self.assertEqual(result.semantic.intent, "stop")
        self.assertEqual(result.queue_status, "emergency_queued")
        self.assertTrue(self.runtime.wait_until_idle(timeout_sec=3))

    def test_english_stop_is_emergency_queued(self) -> None:
        result = self.runtime.process_text("stop")
        self.assertTrue(result.accepted, result.message)
        self.assertEqual(result.semantic.intent, "stop")
        self.assertEqual(result.queue_status, "emergency_queued")
        self.assertTrue(self.runtime.wait_until_idle(timeout_sec=3))

    def test_dangerous_command_is_rejected(self) -> None:
        result = self.runtime.process_text("攻击他")
        self.assertFalse(result.accepted)
        self.assertEqual(result.stage, "safety")
        self.assertIn("dangerous", result.message)

    def test_english_dangerous_command_is_rejected(self) -> None:
        result = self.runtime.process_text("charge forward and hit him")
        self.assertFalse(result.accepted)
        self.assertEqual(result.stage, "safety")
        self.assertIn("dangerous", result.message)

    def test_too_long_duration_is_rejected(self) -> None:
        result = self.runtime.process_text("向前走100秒")
        self.assertFalse(result.accepted)
        self.assertIn("exceeds max", result.message)

    def test_fast_request_is_rejected(self) -> None:
        result = self.runtime.process_text("快点向前走")
        self.assertFalse(result.accepted)
        self.assertIn("speed level", result.message)

    def test_non_command_chat_is_not_queued(self) -> None:
        result = self.runtime.process_text("today is a good day")
        self.assertFalse(result.accepted)
        self.assertEqual(result.stage, "semantic")
        self.assertEqual(result.semantic.is_command, False)
        self.assertEqual(result.queue_status, "not_submitted")


class RuleBasedNluTest(unittest.TestCase):
    def test_mixed_language_command(self) -> None:
        result = QwenEngine({"provider": "rule_based"}).parse_command("机器狗 move forward one second")
        self.assertTrue(result.is_command)
        self.assertEqual(result.intent, "move_forward")
        self.assertEqual(result.source_language, "mixed")


if __name__ == "__main__":
    unittest.main()
