from __future__ import annotations

import math
import wave
from array import array
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AudioDiagnostics:
    audio_path: str
    exists: bool
    audio_file_size: int = 0
    sample_rate: int = 0
    channels: int = 0
    duration_sec: float = 0.0
    peak_amplitude: float = 0.0
    rms_amplitude: float = 0.0
    is_silent_like: bool = False
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def valid_audio(self) -> bool:
        return self.exists and not self.error_message and self.duration_sec > 0


def analyze_audio_file(
    audio_path: str | Path,
    silence_rms_threshold: float = 0.01,
    min_file_bytes: int = 512,
) -> AudioDiagnostics:
    target = Path(audio_path)
    if not target.exists():
        return AudioDiagnostics(
            audio_path=str(target),
            exists=False,
            error_message=f"音频文件不存在：{target}",
        )

    file_size = target.stat().st_size
    if file_size < min_file_bytes:
        return AudioDiagnostics(
            audio_path=str(target),
            exists=True,
            audio_file_size=file_size,
            is_silent_like=True,
            error_message="录音文件过小，可能没有写入有效音频。",
        )

    if target.suffix.lower() == ".wav":
        try:
            return _analyze_wav(target, file_size, silence_rms_threshold)
        except Exception as exc:
            wave_error = f"{exc.__class__.__name__}: {exc}"
    else:
        wave_error = "非 WAV 文件，使用 soundfile 尝试读取。"

    try:
        return _analyze_with_soundfile(target, file_size, silence_rms_threshold)
    except Exception as exc:
        return AudioDiagnostics(
            audio_path=str(target),
            exists=True,
            audio_file_size=file_size,
            error_message=f"音频格式无法读取：{wave_error}; soundfile: {exc}",
        )


def copy_recent_audio(source: str | Path, destination: str | Path) -> Path:
    import shutil

    src = Path(source)
    dst = Path(destination)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return dst


def _analyze_wav(
    target: Path,
    file_size: int,
    silence_rms_threshold: float,
) -> AudioDiagnostics:
    with wave.open(str(target), "rb") as wav:
        channels = wav.getnchannels()
        sample_rate = wav.getframerate()
        sample_width = wav.getsampwidth()
        frames = wav.getnframes()
        duration_sec = frames / float(sample_rate) if sample_rate else 0.0
        raw = wav.readframes(frames)

    peak, rms = _pcm_peak_rms(raw, sample_width)
    return AudioDiagnostics(
        audio_path=str(target),
        exists=True,
        audio_file_size=file_size,
        sample_rate=sample_rate,
        channels=channels,
        duration_sec=duration_sec,
        peak_amplitude=peak,
        rms_amplitude=rms,
        is_silent_like=rms < silence_rms_threshold,
    )


def _analyze_with_soundfile(
    target: Path,
    file_size: int,
    silence_rms_threshold: float,
) -> AudioDiagnostics:
    import soundfile as sf  # type: ignore

    data, sample_rate = sf.read(str(target), always_2d=True, dtype="float32")
    channels = int(data.shape[1]) if hasattr(data, "shape") and len(data.shape) > 1 else 1
    frames = int(data.shape[0]) if hasattr(data, "shape") else 0
    duration_sec = frames / float(sample_rate) if sample_rate else 0.0
    peak = float(abs(data).max()) if frames else 0.0
    rms = float(math.sqrt(float((data * data).mean()))) if frames else 0.0
    return AudioDiagnostics(
        audio_path=str(target),
        exists=True,
        audio_file_size=file_size,
        sample_rate=int(sample_rate),
        channels=channels,
        duration_sec=duration_sec,
        peak_amplitude=peak,
        rms_amplitude=rms,
        is_silent_like=rms < silence_rms_threshold,
    )


def _pcm_peak_rms(raw: bytes, sample_width: int) -> tuple[float, float]:
    if not raw:
        return 0.0, 0.0
    if sample_width == 1:
        samples = [(byte - 128) / 128.0 for byte in raw]
    elif sample_width == 2:
        values = array("h")
        values.frombytes(raw)
        samples = [sample / 32768.0 for sample in values]
    elif sample_width == 4:
        values = array("i")
        values.frombytes(raw)
        samples = [sample / 2147483648.0 for sample in values]
    elif sample_width == 3:
        samples = []
        for index in range(0, len(raw) - 2, 3):
            chunk = raw[index : index + 3]
            value = int.from_bytes(chunk, "little", signed=False)
            if value & 0x800000:
                value -= 0x1000000
            samples.append(value / 8388608.0)
    else:
        return 0.0, 0.0

    if not samples:
        return 0.0, 0.0
    peak = max(abs(sample) for sample in samples)
    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    return float(peak), float(rms)
