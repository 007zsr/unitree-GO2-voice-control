from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.audio.audio_env import check_audio_dependencies


class AudioDependencyStatusTest(unittest.TestCase):
    def test_missing_sounddevice_is_reported(self) -> None:
        def fake_import(name: str):
            if name == "sounddevice":
                raise ModuleNotFoundError(name)
            return object()

        status = check_audio_dependencies(import_module=fake_import)
        self.assertFalse(status.available)
        self.assertEqual(status.missing_packages, ["sounddevice"])
        self.assertIn("sounddevice", status.user_message())

    def test_missing_soundfile_is_reported(self) -> None:
        def fake_import(name: str):
            if name == "soundfile":
                raise ModuleNotFoundError(name)
            return object()

        status = check_audio_dependencies(import_module=fake_import)
        self.assertFalse(status.available)
        self.assertEqual(status.missing_packages, ["soundfile"])
        self.assertIn("soundfile", status.user_message())

    def test_available_dependencies(self) -> None:
        status = check_audio_dependencies(import_module=lambda name: object())
        self.assertTrue(status.available)
        self.assertEqual(status.missing_packages, [])


if __name__ == "__main__":
    unittest.main()
