from __future__ import annotations

import unittest
from pathlib import Path

from src.config import ConfigSet
from src.runtime.session_runtime import SessionRuntime


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CommandPlanRuntimeTest(unittest.TestCase):
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

    def test_english_sequence_plan_executes_in_order(self) -> None:
        result = self.runtime.process_text("Hi Go2, turn right, and then turn left.")
        self.assertTrue(result.accepted, result.message)
        self.assertIsNotNone(result.command_plan)
        self.assertEqual(result.command_plan.intent_sequence, ["turn_right", "turn_left"])
        self.assertEqual(result.queue_status, "plan_completed")
        self.assertEqual(
            [command.intent for command in self.runtime.adapter.executed],
            ["turn_right", "turn_left"],
        )

    def test_chinese_sequence_plan_executes_in_order(self) -> None:
        result = self.runtime.process_text("先向左转，然后向右转。")
        self.assertTrue(result.accepted, result.message)
        self.assertIsNotNone(result.command_plan)
        self.assertEqual(result.command_plan.intent_sequence, ["turn_left", "turn_right"])

    def test_plan_truncates_after_three_commands(self) -> None:
        result = self.runtime.process_text("stand up, turn right, turn left, sit down")
        self.assertTrue(result.accepted, result.message)
        self.assertIsNotNone(result.command_plan)
        self.assertEqual(result.command_plan.intent_sequence, ["stand_up", "turn_right", "turn_left"])
        self.assertTrue(result.command_plan.truncated)
        self.assertEqual(result.command_plan.truncated_count, 1)

    def test_fuzzy_left_come_here_turns_only(self) -> None:
        result = self.runtime.process_text("I am on your left, please come here.")
        self.assertTrue(result.accepted, result.message)
        self.assertIsNotNone(result.command_plan)
        self.assertEqual(result.command_plan.intent_sequence, ["turn_left"])
        self.assertTrue(result.command_plan.fuzzy_detected)
        self.assertTrue(result.command.inferred)
        self.assertNotIn("move_forward", result.command_plan.intent_sequence)

    def test_fuzzy_right_come_here_turns_only(self) -> None:
        result = self.runtime.process_text("I am on your right, please come here.")
        self.assertTrue(result.accepted, result.message)
        self.assertEqual(result.command_plan.intent_sequence, ["turn_right"])
        self.assertNotIn("move_forward", result.command_plan.intent_sequence)

    def test_come_here_alone_needs_confirmation(self) -> None:
        result = self.runtime.process_text("Come here.")
        self.assertFalse(result.accepted)
        self.assertEqual(result.stage, "confirmation")
        self.assertIsNotNone(result.command_plan)
        self.assertTrue(result.command_plan.needs_confirmation)
        self.assertEqual(result.command_plan.intent_sequence, ["unknown_relative_move"])
        self.assertEqual(self.runtime.adapter.executed, [])

    def test_stop_trims_following_plan_commands(self) -> None:
        result = self.runtime.process_text("turn right, then stop, then turn left")
        self.assertTrue(result.accepted, result.message)
        self.assertEqual(result.command_plan.intent_sequence, ["turn_right", "stop"])
        self.assertEqual(
            [command.intent for command in self.runtime.adapter.executed],
            ["turn_right", "stop"],
        )

    def test_duplicate_plan_is_skipped_in_continuous_mode(self) -> None:
        first = self.runtime.process_text("turn right and then turn left", deduplicate=True)
        second = self.runtime.process_text("please turn right and then turn left", deduplicate=True)
        self.assertTrue(first.accepted, first.message)
        self.assertFalse(second.accepted)
        self.assertEqual(second.stage, "deduplicate")
        self.assertEqual(second.queue_status, "deduplicated")


if __name__ == "__main__":
    unittest.main()
