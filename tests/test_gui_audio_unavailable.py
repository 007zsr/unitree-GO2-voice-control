from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.audio.audio_env import AudioDependencyStatus
from src.gui.gui_runtime_bridge import GuiRuntimeBridge


MISSING_AUDIO = AudioDependencyStatus(
    available=False,
    missing_packages=["sounddevice", "soundfile"],
    message="missing audio deps",
)


class GuiAudioUnavailableTest(unittest.TestCase):
    def _build_bridge(self) -> GuiRuntimeBridge:
        bridge = GuiRuntimeBridge(PROJECT_ROOT / "configs")
        bridge.configs.app["robot_mode"] = "mock"
        bridge.configs.app["enable_real_robot"] = False
        bridge.configs.go2["robot_mode"] = "mock"
        bridge.configs.go2["enable_real_robot"] = False
        bridge.start()
        return bridge

    def test_text_mode_still_works_without_audio_dependencies(self) -> None:
        with patch("src.gui.gui_runtime_bridge.check_audio_dependencies", return_value=MISSING_AUDIO):
            bridge = self._build_bridge()
            try:
                result = bridge.process_text_once("向前走一秒")
                self.assertTrue(result.accepted, result.message)
                self.assertEqual(result.semantic_result["intent"], "move_forward")
            finally:
                bridge.shutdown()

    def test_process_audio_once_returns_audio_dependency_error(self) -> None:
        with patch("src.gui.gui_runtime_bridge.check_audio_dependencies", return_value=MISSING_AUDIO):
            bridge = self._build_bridge()
            try:
                result = bridge.process_audio_once("missing.wav", input_type="one_shot_audio")
                self.assertFalse(result.accepted)
                self.assertEqual(result.error_stage, "audio_dependency")
                self.assertIn("sounddevice", result.message)
                self.assertEqual(result.queue_result, "not_started")
            finally:
                bridge.shutdown()

    def test_continuous_listening_does_not_start_when_audio_unavailable(self) -> None:
        with patch("src.gui.gui_runtime_bridge.check_audio_dependencies", return_value=MISSING_AUDIO):
            bridge = self._build_bridge()
            results = []
            events = []
            try:
                started = bridge.start_continuous_listening(results.append, events.append)
                self.assertFalse(started)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].error_stage, "audio_dependency")
                self.assertIsNone(bridge._listener)
                self.assertEqual(events, ["未监听"])
            finally:
                bridge.shutdown()


if __name__ == "__main__":
    unittest.main()
