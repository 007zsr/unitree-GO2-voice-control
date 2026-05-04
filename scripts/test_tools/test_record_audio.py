from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from src.audio.audio_capture import AudioCapture
from src.audio.audio_diagnostics import analyze_audio_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a short microphone sample")
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--device", default="default")
    parser.add_argument(
        "--output",
        default=str(_bootstrap.PROJECT_ROOT / "runtime_data" / "debug_audio" / "last_record.wav"),
    )
    args = parser.parse_args()

    target = Path(args.output)
    capture = AudioCapture(input_device=args.device)
    print(f"Recording {args.duration:.1f}s to {target} ...")
    capture.record_to_file(target, args.duration)
    diagnostics = analyze_audio_file(target)

    print(f"saved: {target.exists()}")
    print(f"path: {target}")
    print(f"file_size: {diagnostics.audio_file_size}")
    print(f"sample_rate: {diagnostics.sample_rate}")
    print(f"duration_sec: {diagnostics.duration_sec:.3f}")
    print(f"channels: {diagnostics.channels}")
    print(f"peak_amplitude: {diagnostics.peak_amplitude:.6f}")
    print(f"rms_amplitude: {diagnostics.rms_amplitude:.6f}")
    print(f"is_silent_like: {diagnostics.is_silent_like}")
    if diagnostics.error_message:
        print(f"error: {diagnostics.error_message}")
        return 2
    if diagnostics.is_silent_like:
        print("录音音量过低，可能没有录到人声或麦克风设备错误。")
        return 3
    print("录音诊断通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
