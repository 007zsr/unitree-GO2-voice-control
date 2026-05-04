from __future__ import annotations

from pathlib import Path
from typing import Any

from src.audio.audio_env import AudioDependencyError, check_audio_dependencies


class AudioCapture:
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        input_device: str | int | None = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.input_device = None if input_device in (None, "", "default") else input_device

    def record_to_file(self, output_path: str | Path, duration_sec: float) -> Path:
        audio = self.record_array(duration_sec)
        return self.write_array_to_file(output_path, audio)

    def record_array(self, duration_sec: float) -> Any:
        status = check_audio_dependencies()
        if not status.available:
            raise AudioDependencyError(status)

        import sounddevice as sd  # type: ignore

        frames = int(duration_sec * self.sample_rate)
        audio = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.input_device,
        )
        sd.wait()
        return audio

    def write_array_to_file(self, output_path: str | Path, audio: Any) -> Path:
        status = check_audio_dependencies()
        if not status.available:
            raise AudioDependencyError(status)

        import soundfile as sf  # type: ignore

        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(target), audio, self.sample_rate)
        return target
