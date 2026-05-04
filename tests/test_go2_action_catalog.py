from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPT_CHECK_DIR = PROJECT_ROOT / "scripts" / "check"
if str(SCRIPT_CHECK_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_CHECK_DIR))

from scan_go2_sport_actions import SourceText, parse_sport_sources
from src.commands.command_catalog import CommandCatalog
from src.config import ConfigSet
from src.models import RobotState
from src.runtime.session_runtime import SessionRuntime
from src.safety.safety_controller import SafetyController


class Go2ActionCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.configs = ConfigSet.load(PROJECT_ROOT / "configs")
        self.configs.app["robot_mode"] = "mock"
        self.configs.app["enable_real_robot"] = False
        self.configs.go2["robot_mode"] = "mock"
        self.configs.go2["enable_real_robot"] = False

    def test_catalog_loads_official_dangerous_action(self) -> None:
        catalog = CommandCatalog(self.configs.commands, self.configs.go2_actions)
        front_flip = catalog.require("front_flip")
        self.assertEqual(front_flip.sdk_method, "FrontFlip")
        self.assertEqual(front_flip.risk_level, "dangerous")
        self.assertFalse(front_flip.real_robot_enabled)

    def test_dangerous_voice_action_is_recognized_but_not_queued(self) -> None:
        runtime = SessionRuntime(self.configs)
        runtime.start()
        try:
            result = runtime.process_text("front flip")
            self.assertFalse(result.accepted)
            self.assertEqual(result.stage, "confirmation")
            self.assertEqual(result.semantic.intent, "front_flip")
            self.assertEqual(result.semantic.risk_level, "dangerous")
            self.assertFalse(result.semantic.executable)
            self.assertEqual(result.queue_status, "not_submitted")
        finally:
            runtime.shutdown()

    def test_dangerous_word_takes_priority_over_safe_action(self) -> None:
        runtime = SessionRuntime(self.configs)
        runtime.start()
        try:
            result = runtime.process_text("turn right jump")
            self.assertFalse(result.accepted)
            self.assertEqual(result.stage, "safety")
            self.assertIn("dangerous", result.message)
            self.assertEqual(self.runtime_executed(runtime), [])
        finally:
            runtime.shutdown()

    def test_caution_action_simulates_in_mock(self) -> None:
        runtime = SessionRuntime(self.configs)
        runtime.start()
        try:
            result = runtime.process_text("dance")
            self.assertTrue(result.accepted, result.message)
            self.assertEqual(result.semantic.intent, "dance1")
            self.assertEqual(result.semantic.risk_level, "caution")
            self.assertEqual(result.plan_results[0]["adapter_result"]["message"], "Mock: dance1 simulated")
        finally:
            runtime.shutdown()

    def test_real_robot_safety_rejects_caution_and_dangerous_actions(self) -> None:
        catalog = CommandCatalog(self.configs.commands, self.configs.go2_actions)
        safety = SafetyController(
            self.configs.safety,
            catalog,
            robot_mode="go2",
            enable_real_robot=True,
        )
        state = RobotState(connected=True, standing=True, mode="go2")

        dance_semantic = self._semantic(runtime_text="dance", intent="dance1")
        dance_command = self._command_for("dance", "dance1")
        dance_decision = safety.check(dance_semantic, dance_command, state)
        self.assertFalse(dance_decision.allowed)
        self.assertIn("caution action disabled", dance_decision.reason)

        flip_semantic = self._semantic(runtime_text="front flip", intent="front_flip")
        flip_semantic.need_clarification = False
        flip_semantic.executable = True
        flip_command = self._command_for("front flip", "front_flip")
        flip_decision = safety.check(flip_semantic, flip_command, state)
        self.assertFalse(flip_decision.allowed)
        self.assertIn("dangerous action disabled", flip_decision.reason)

    def test_scan_parser_extracts_registered_and_method_actions(self) -> None:
        client = SourceText(
            "sport_client.py",
            "memory://sport_client.py",
            "class SportClient(Client): "
            "def Init(self): "
            "self._RegistApi(SPORT_API_ID_FRONTFLIP, 0) # FrontFlip "
            "def FrontFlip(self): "
            "p = {} "
            "code, data = self._Call(SPORT_API_ID_FRONTFLIP, json.dumps(p)) "
            "return code",
        )
        api = SourceText("sport_api.py", "memory://sport_api.py", "SPORT_API_ID_FRONTFLIP = 1030")
        records = parse_sport_sources([client, api])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].official_name, "FrontFlip")
        self.assertEqual(records[0].sdk_method, "FrontFlip")
        self.assertEqual(records[0].sdk_api_id, 1030)

    def _semantic(self, runtime_text: str, intent: str):
        runtime = SessionRuntime(self.configs)
        try:
            return runtime.qwen.parse_command(runtime_text)
        finally:
            runtime.shutdown()

    def _command_for(self, runtime_text: str, intent: str):
        runtime = SessionRuntime(self.configs)
        try:
            semantic = runtime.qwen.parse_command(runtime_text)
            semantic.need_clarification = False
            semantic.executable = True
            return runtime.normalizer.normalize(semantic, runtime_text)
        finally:
            runtime.shutdown()

    def runtime_executed(self, runtime: SessionRuntime) -> list[str]:
        return [command.intent for command in getattr(runtime.adapter, "executed", [])]


if __name__ == "__main__":
    unittest.main()
