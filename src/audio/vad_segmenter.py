from __future__ import annotations

from pathlib import Path
from typing import Any

from src.audio.audio_capture import AudioCapture
from src.models import new_command_id


class FixedChunkSegmenter:
    """First-stage microphone segmenter using fixed-duration chunks."""

    def __init__(
        self,
        audio_capture: AudioCapture,
        temp_dir: str | Path,
        chunk_sec: float = 3.0,
    ):
        self.audio_capture = audio_capture
        self.temp_dir = Path(temp_dir)
        self.chunk_sec = chunk_sec

    def record_next_segment(self) -> Path:
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        target = self.temp_dir / f"{new_command_id()}.wav"
        return self.audio_capture.record_to_file(target, self.chunk_sec)


class RollingWindowSegmenter:
    """Microphone segmenter using a rolling window with overlap.

    The first call records a full window. Later calls record only ``hop_sec`` and
    write the latest ``window_sec`` of audio. This is not true streaming ASR, but
    it avoids cutting short commands exactly on a fixed chunk boundary.
    """

    def __init__(
        self,
        audio_capture: AudioCapture,
        temp_dir: str | Path,
        window_sec: float = 4.0,
        hop_sec: float = 1.5,
    ):
        self.audio_capture = audio_capture
        self.temp_dir = Path(temp_dir)
        self.window_sec = max(float(window_sec), 1.0)
        self.hop_sec = max(float(hop_sec), 0.25)
        self._buffer: Any | None = None

    def record_next_segment(self) -> Path:
        import numpy as np  # type: ignore

        self.temp_dir.mkdir(parents=True, exist_ok=True)
        record_sec = self.window_sec if self._buffer is None else self.hop_sec
        new_audio = self.audio_capture.record_array(record_sec)
        if self._buffer is None:
            self._buffer = new_audio
        else:
            self._buffer = np.concatenate([self._buffer, new_audio], axis=0)
        max_frames = int(self.window_sec * self.audio_capture.sample_rate)
        if len(self._buffer) > max_frames:
            self._buffer = self._buffer[-max_frames:]
        target = self.temp_dir / f"{new_command_id()}_rolling.wav"
        return self.audio_capture.write_array_to_file(target, self._buffer)
