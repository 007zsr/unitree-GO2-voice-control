from __future__ import annotations

import argparse
import json

import _bootstrap  # noqa: F401
from src.asr.asr_env import check_asr_dependencies, resolve_whisper_model_dir
from src.config import ConfigSet


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Whisper ASR environment")
    parser.add_argument("--config-dir", default=str(_bootstrap.PROJECT_ROOT / "configs"))
    args = parser.parse_args()

    configs = ConfigSet.load(args.config_dir)
    asr_config = configs.models.get("asr", {})
    whisper_config = configs.models.get("whisper", {})
    model_name = str(
        asr_config.get("model_size")
        or (whisper_config.get("name") if isinstance(whisper_config, dict) else "")
        or "base"
    )
    model_dir = resolve_whisper_model_dir(asr_config if isinstance(asr_config, dict) else {})
    status = check_asr_dependencies(model_name=model_name, model_dir=model_dir)

    print(f"Project root: {status.project_root}")
    print(f"Python executable: {status.python_executable}")
    print(f"Python version: {status.python_version}")
    print(f"Is project venv: {'true' if status.is_project_venv else 'false'}")
    print(f"Project venv path: {status.project_venv_path}")
    print(f"Whisper: {'OK' if status.whisper_available else 'MISSING'}")
    if status.whisper_package_path:
        print(f"Whisper path: {status.whisper_package_path}")
    else:
        print("Whisper path: -")
    print(f"ffmpeg: {'OK' if status.ffmpeg_available else 'MISSING'}")
    if status.ffmpeg_path:
        print(f"ffmpeg path: {status.ffmpeg_path}")
    else:
        print("ffmpeg path: -")
    print(f"Whisper model name: {status.model_name}")
    print(f"Whisper model directory: {status.whisper_model_dir}")
    print(f"Whisper model files found: {'true' if status.whisper_model_files_found else 'false'}")
    if status.whisper_model_files:
        print(f"Whisper model files: {', '.join(status.whisper_model_files)}")
    print(f"ASR status: {'OK' if status.available else 'FAIL'}")
    print(f"Missing dependencies: {', '.join(status.missing_dependencies or status.missing or []) or '-'}")
    if not status.is_project_venv:
        print("WARN: 当前 Python 不是项目 .venv，依赖可能来自系统 Python 或用户目录。")
    if status.whisper_available and not status.whisper_model_files_found:
        print("WARN: Whisper 包已安装，但项目内模型目录暂无模型文件，首次运行会下载到 models/whisper。")
    print("details:")
    print(json.dumps(status.to_dict(), ensure_ascii=False, indent=2))
    if not status.available:
        print("\n修复建议：")
        print(status.user_message())
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
