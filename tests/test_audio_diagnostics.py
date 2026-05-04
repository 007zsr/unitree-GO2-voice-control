from __future__ import annotations

import math
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.asr.whisper_engine import WhisperEngine
from src.audio.audio_diagnostics import analyze_audio_file


class AudioDiagnosticsTest(unittest.TestCase):
    def test_silent_wav_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "silent.wav"
            self._write_wav(path, [0] * 16000)
            diagnostics = analyze_audio_file(path)
            self.assertEqual(diagnostics.sample_rate, 16000)
            self.assertAlmostEqual(diagnostics.duration_sec, 1.0, places=2)
            self.assertTrue(diagnostics.is_silent_like)
            self.assertEqual(diagnostics.rms_amplitude, 0.0)

    def test_loud_wav_is_not_silent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "voice_like.wav"
            samples = [
                int(12000 * math.sin(2 * math.pi * 440 * index / 16000))
                for index in range(16000)
            ]
            self._write_wav(path, samples)
            diagnostics = analyze_audio_file(path)
            self.assertFalse(diagnostics.is_silent_like)
            self.assertGreater(diagnostics.rms_amplitude, 0.1)

    def test_whisper_engine_returns_diagnostic_for_silent_audio(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "silent.wav"
            self._write_wav(path, [0] * 16000)
            result = WhisperEngine({"model_size": "base"}).transcribe(path)
            self.assertEqual(result.text, "")
            self.assertTrue(result.is_silent_like)
            self.assertFalse(result.whisper_executed)
            self.assertIn("音量过低", result.error_message)

    def _write_wav(self, path: Path, samples: list[int]) -> None:
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))


if __name__ == "__main__":
    unittest.main()
