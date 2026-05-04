from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.audio.audio_env import check_audio_dependencies


def main() -> int:
    parser = argparse.ArgumentParser(description="List audio input/output devices")
    parser.parse_args()

    status = check_audio_dependencies(query_devices=False)
    if not status.available:
        print(status.user_message())
        return 2

    import sounddevice as sd  # type: ignore

    print("Default devices:", sd.default.device)
    devices = sd.query_devices()
    input_count = 0
    for index, device in enumerate(devices):
        max_input = int(device.get("max_input_channels", 0))
        marker = "INPUT" if max_input > 0 else "-----"
        if max_input > 0:
            input_count += 1
        print(
            f"[{index:02d}] {marker} "
            f"name={device.get('name')} "
            f"max_input_channels={max_input} "
            f"default_samplerate={device.get('default_samplerate')}"
        )

    if input_count == 0:
        print("No audio input device found.")
        return 3
    print(f"Input devices found: {input_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
