from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.asr.asr_env import check_asr_dependencies


class AsrDependencyStatusTest(unittest.TestCase):
    def test_missing_whisper_is_reported(self) -> None:
        def fake_import(name: str):
            if name == "whisper":
                raise ModuleNotFoundError(name)
            return object()

        status = check_asr_dependencies(
            model_name="base",
            import_module=fake_import,
            which=lambda name: "ffmpeg",
        )
        self.assertFalse(status.available)
        self.assertFalse(status.whisper_available)
        self.assertTrue(status.ffmpeg_available)
        self.assertIn("openai-whisper", status.missing)
        self.assertIn("openai-whisper", status.missing_dependencies)
        self.assertIn("openai-whisper", status.user_message())
        self.assertIn("python -m pip install -U openai-whisper", status.user_message())
        self.assertNotIn("winget install --id Gyan.FFmpeg -e", status.user_message())

    def test_missing_ffmpeg_is_reported(self) -> None:
        status = check_asr_dependencies(
            model_name="base",
            import_module=lambda name: object(),
            which=lambda name: None,
        )
        self.assertFalse(status.available)
        self.assertTrue(status.whisper_available)
        self.assertFalse(status.ffmpeg_available)
        self.assertIn("ffmpeg", status.missing)
        self.assertIn("ffmpeg", status.missing_dependencies)
        self.assertIn("ffmpeg", status.user_message())
        self.assertIn("winget install --id Gyan.FFmpeg -e", status.user_message())
        self.assertIn("ffmpeg -version", status.user_message())
        self.assertNotIn("python -m pip install -U openai-whisper", status.user_message())

    def test_missing_both_dependencies_are_reported_separately(self) -> None:
        def fake_import(name: str):
            if name == "whisper":
                raise ModuleNotFoundError(name)
            return object()

        status = check_asr_dependencies(
            model_name="base",
            import_module=fake_import,
            which=lambda name: None,
        )
        self.assertFalse(status.available)
        self.assertFalse(status.whisper_available)
        self.assertFalse(status.ffmpeg_available)
        self.assertEqual(status.missing_dependencies, ["openai-whisper", "ffmpeg"])
        self.assertIn("python -m pip install -U openai-whisper", status.user_message())
        self.assertIn("winget install --id Gyan.FFmpeg -e", status.user_message())

    def test_available_asr_dependencies(self) -> None:
        status = check_asr_dependencies(
            model_name="tiny",
            import_module=lambda name: object(),
            which=lambda name: "/usr/bin/ffmpeg",
        )
        self.assertTrue(status.available)
        self.assertEqual(status.model_name, "tiny")


if __name__ == "__main__":
    unittest.main()
