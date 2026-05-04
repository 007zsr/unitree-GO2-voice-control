from __future__ import annotations

import argparse
import json

import _bootstrap  # noqa: F401
from src.asr.asr_env import check_asr_dependencies, resolve_whisper_model_dir
from src.asr.whisper_engine import WhisperEngine
from src.config import ConfigSet


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Whisper on one audio file")
    parser.add_argument("--audio", required=True)
    parser.add_argument("--config-dir", default=str(_bootstrap.PROJECT_ROOT / "configs"))
    args = parser.parse_args()

    configs = ConfigSet.load(args.config_dir)
    asr_config = configs.models.get("asr", {})
    whisper_config = configs.models.get("whisper", {})
    if isinstance(whisper_config, dict):
        for key in [
            "language",
            "task",
            "fp16",
            "temperature",
            "condition_on_previous_text",
            "initial_prompt",
        ]:
            if key in whisper_config and key not in asr_config:
                asr_config[key] = whisper_config[key]
    model_dir = resolve_whisper_model_dir(asr_config if isinstance(asr_config, dict) else {})
    env_status = check_asr_dependencies(
        model_name=str(asr_config.get("model_size", "base")),
        model_dir=model_dir,
    )
    print(f"Whisper import: {'OK' if env_status.whisper_available else 'NOT INSTALLED'}")
    print(f"ffmpeg: {'OK' if env_status.ffmpeg_available else 'NOT FOUND'}")
    print(f"Whisper model directory: {env_status.whisper_model_dir}")
    if not env_status.available:
        print(env_status.user_message())
        return 2

    engine = WhisperEngine(asr_config)
    result = engine.transcribe(args.audio)

    print(f"Whisper model: {asr_config.get('model_size', 'base')}")
    print(f"Language config: {result.language_config}")
    print(f"Task: {result.task}")
    print(f"Audio path: {result.audio_path}")
    print(f"Duration: {result.duration_sec:.3f}s")
    print(f"Sample rate: {result.sample_rate}")
    print(f"Channels: {result.channels}")
    print(f"Peak: {result.peak_amplitude:.6f}")
    print(f"RMS: {result.rms_amplitude:.6f}")
    print(f"Silent-like: {result.is_silent_like}")
    print(f"Whisper loaded: {result.whisper_loaded}")
    print(f"Whisper executed: {result.whisper_executed}")
    print(f"Text: {result.text}")
    print(f"Detected language: {result.language}")
    print(f"no_speech_prob: {result.no_speech_prob:.3f}")
    print(f"segments_count: {result.segments_count}")
    print(f"segments_text_preview: {result.segments_text_preview}")
    print(f"raw_result_keys: {result.raw_result_keys}")
    print(f"reason_guess: {result.reason_guess}")
    if result.error_message:
        print(f"diagnosis: {result.error_message}")
    raw_summary = {
        "keys": result.raw_result_keys,
        "segment_count": result.segments_count,
        "segments_text_preview": result.segments_text_preview,
    }
    print("raw_result_summary:")
    print(json.dumps(raw_summary, ensure_ascii=False, indent=2))

    if not result.text:
        if result.whisper_executed:
            print(
                "Whisper executed but returned empty text. Check audio volume, "
                "speech length, microphone device, and language settings."
            )
        else:
            print("Whisper did not execute or audio was skipped before ASR. Check diagnostics first.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
