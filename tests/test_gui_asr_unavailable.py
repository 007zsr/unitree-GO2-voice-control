from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.asr.asr_env import AsrDependencyStatus
from src.audio.audio_env import AudioDependencyStatus
from src.gui.gui_runtime_bridge import GuiRuntimeBridge


AVAILABLE_AUDIO = AudioDependencyStatus(available=True, message="audio ok")
MISSING_ASR = AsrDependencyStatus(
    available=False,
    whisper_available=False,
    ffmpeg_available=False,
    python_executable=sys.executable,
    python_version=sys.version.split()[0],
    model_name="base",
    missing=["openai-whisper", "ffmpeg"],
    missing_dependencies=["openai-whisper", "ffmpeg"],
    message="missing asr",
)
MISSING_FFMPEG_ONLY = AsrDependencyStatus(
    available=False,
    whisper_available=True,
    ffmpeg_available=False,
    python_executable=sys.executable,
    python_version=sys.version.split()[0],
    whisper_package_path="site-packages/whisper/__init__.py",
    model_name="base",
    missing=["ffmpeg"],
    missing_dependencies=["ffmpeg"],
    message="missing ffmpeg",
)


class GuiAsrUnavailableTest(unittest.TestCase):
    def _build_bridge(self) -> GuiRuntimeBridge:
        bridge = GuiRuntimeBridge(PROJECT_ROOT / "configs")
        bridge.configs.app["robot_mode"] = "mock"
        bridge.configs.app["enable_real_robot"] = False
        bridge.configs.go2["robot_mode"] = "mock"
        bridge.configs.go2["enable_real_robot"] = False
        bridge.start()
        return bridge

    def test_text_mode_still_works_without_asr(self) -> None:
        with (
            patch("src.gui.gui_runtime_bridge.check_audio_dependencies", return_value=AVAILABLE_AUDIO),
            patch("src.gui.gui_runtime_bridge.check_asr_dependencies", return_value=MISSING_ASR),
        ):
            bridge = self._build_bridge()
            try:
                result = bridge.process_text_once("向前走一秒")
                self.assertTrue(result.accepted, result.message)
                self.assertEqual(result.semantic_result["intent"], "move_forward")
            finally:
                bridge.shutdown()

    def test_process_audio_once_returns_asr_dependency_error(self) -> None:
        with (
            patch("src.gui.gui_runtime_bridge.check_audio_dependencies", return_value=AVAILABLE_AUDIO),
            patch("src.gui.gui_runtime_bridge.check_asr_dependencies", return_value=MISSING_ASR),
        ):
            bridge = self._build_bridge()
            try:
                result = bridge.process_audio_once("some.wav", input_type="one_shot_audio")
                self.assertFalse(result.accepted)
                self.assertEqual(result.error_stage, "asr_dependency")
                self.assertIn("openai-whisper", result.message)
                self.assertEqual(result.queue_result, "not_started")
            finally:
                bridge.shutdown()

    def test_process_audio_once_reports_ffmpeg_without_whisper_install_hint(self) -> None:
        with (
            patch("src.gui.gui_runtime_bridge.check_audio_dependencies", return_value=AVAILABLE_AUDIO),
            patch("src.gui.gui_runtime_bridge.check_asr_dependencies", return_value=MISSING_FFMPEG_ONLY),
        ):
            bridge = self._build_bridge()
            try:
                result = bridge.process_audio_once("some.wav", input_type="one_shot_audio")
                self.assertFalse(result.accepted)
                self.assertEqual(result.error_stage, "asr_dependency")
                self.assertIn("ffmpeg", result.message)
                self.assertIn("winget install --id Gyan.FFmpeg -e", result.message)
                self.assertNotIn("python -m pip install -U openai-whisper", result.message)
            finally:
                bridge.shutdown()

    def test_continuous_listening_does_not_start_when_asr_unavailable(self) -> None:
        with (
            patch("src.gui.gui_runtime_bridge.check_audio_dependencies", return_value=AVAILABLE_AUDIO),
            patch("src.gui.gui_runtime_bridge.check_asr_dependencies", return_value=MISSING_ASR),
        ):
            bridge = self._build_bridge()
            results = []
            events = []
            try:
                started = bridge.start_continuous_listening(results.append, events.append)
                self.assertFalse(started)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].error_stage, "asr_dependency")
                self.assertIsNone(bridge._listener)
                self.assertEqual(events, ["未监听"])
            finally:
                bridge.shutdown()

    def test_one_shot_voice_does_not_record_when_asr_unavailable(self) -> None:
        with (
            patch("src.gui.gui_runtime_bridge.check_audio_dependencies", return_value=AVAILABLE_AUDIO),
            patch("src.gui.gui_runtime_bridge.check_asr_dependencies", return_value=MISSING_ASR),
        ):
            bridge = self._build_bridge()
            results = []
            events = []
            try:
                started = bridge.start_one_shot_voice(results.append, events.append)
                self.assertFalse(started)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].error_stage, "asr_dependency")
                self.assertIsNone(bridge._one_shot)
                self.assertEqual(events, ["空闲"])
            finally:
                bridge.shutdown()


if __name__ == "__main__":
    unittest.main()
