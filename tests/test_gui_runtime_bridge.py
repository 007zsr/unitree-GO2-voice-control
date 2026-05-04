from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.gui import gui_runtime_bridge
from src.gui.gui_runtime_bridge import GuiRuntimeBridge


class GuiRuntimeBridgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = GuiRuntimeBridge(PROJECT_ROOT / "configs")
        self.bridge.configs.app["robot_mode"] = "mock"
        self.bridge.configs.app["enable_real_robot"] = False
        self.bridge.configs.go2["robot_mode"] = "mock"
        self.bridge.configs.go2["enable_real_robot"] = False
        self.bridge.start()

    def tearDown(self) -> None:
        self.bridge.shutdown()

    def test_text_command_uses_pipeline_and_mock_accepts(self) -> None:
        result = self.bridge.process_text_once("向前走一秒")
        self.assertTrue(result.accepted, result.message)
        self.assertEqual(result.semantic_result["intent"], "move_forward")
        self.assertEqual(result.safety_decision["allowed"], True)
        self.assertEqual(result.queue_result, "queued")
        self.assertIsNotNone(result.adapter_result)
        self.assertTrue(result.adapter_result["success"])

    def test_dangerous_text_is_rejected_by_safety(self) -> None:
        result = self.bridge.process_text_once("攻击那个人")
        self.assertFalse(result.accepted)
        self.assertEqual(result.stage, "safety")
        self.assertEqual(result.semantic_result["dangerous"], True)
        self.assertIn("dangerous", result.message)

    def test_non_command_text_does_not_enter_queue(self) -> None:
        result = self.bridge.process_text_once("今天天气很好")
        self.assertFalse(result.accepted)
        self.assertEqual(result.stage, "semantic")
        self.assertEqual(result.semantic_result["is_command"], False)
        self.assertIsNone(result.robot_command)
        self.assertEqual(result.queue_result, "not_submitted")
        self.assertIsNone(result.adapter_result)

    def test_emergency_stop_submits_stop(self) -> None:
        result = self.bridge.submit_emergency_stop()
        self.assertTrue(result.accepted, result.message)
        self.assertEqual(result.semantic_result["intent"], "stop")
        self.assertEqual(result.queue_result, "emergency_queued")

    def test_bridge_does_not_import_sdk_or_adapters(self) -> None:
        source = inspect.getsource(gui_runtime_bridge)
        self.assertNotIn("unitree_sdk2py", source)
        self.assertNotIn("Go2Adapter", source)
        self.assertNotIn("MockAdapter", source)


if __name__ == "__main__":
    unittest.main()
