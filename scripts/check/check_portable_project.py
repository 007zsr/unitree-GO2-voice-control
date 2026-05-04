from __future__ import annotations

from pathlib import Path

import _bootstrap  # noqa: F401
from src.asr.asr_env import check_asr_dependencies, is_project_venv_python, resolve_project_path
from src.config import ConfigSet


def _inside(path_text: str, parent: Path) -> bool:
    try:
        Path(path_text).resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def main() -> int:
    project_root = _bootstrap.PROJECT_ROOT.resolve()
    configs = ConfigSet.load(project_root / "configs")
    asr_config = configs.models.get("asr", {})
    qwen_config = configs.models.get("qwen", {})
    whisper_model_dir = resolve_project_path(
        str(asr_config.get("download_root") or asr_config.get("model_dir") or "models/whisper"),
        project_root,
    )
    qwen_model_dir = resolve_project_path(
        str(qwen_config.get("local_model_dir") or "models/qwen"),
        project_root,
    )
    asr_status = check_asr_dependencies(
        model_name=str(asr_config.get("model_size", "base")),
        model_dir=whisper_model_dir,
        project_root_path=project_root,
    )

    issues: list[str] = []
    warnings: list[str] = []
    if not is_project_venv_python(asr_status.python_executable, project_root):
        warnings.append("Python is not from project .venv")
    if asr_status.whisper_package_path and not _inside(asr_status.whisper_package_path, project_root / ".venv"):
        warnings.append("Whisper package is not from project .venv")
    if not _inside(asr_status.whisper_model_dir, project_root / "models" / "whisper"):
        issues.append("Whisper model directory is not models/whisper")
    provider = str(qwen_config.get("provider") or qwen_config.get("mode") or "rule_based")
    if provider in {"rule_based", "mock", "local_rule"}:
        qwen_state = "rule_based"
    else:
        qwen_state = str(qwen_model_dir)
        if not _inside(str(qwen_model_dir), project_root / "models" / "qwen"):
            issues.append("Qwen local model directory is not models/qwen")
        if not qwen_model_dir.exists():
            issues.append("Qwen local mode is configured but models/qwen is missing")
    if not asr_status.ffmpeg_available:
        issues.append("ffmpeg is not available")

    if issues:
        portable_status = "PORTABLE_FAIL"
        exit_code = 2
    elif warnings:
        portable_status = "PORTABLE_WARN"
        exit_code = 1
    else:
        portable_status = "PORTABLE_OK"
        exit_code = 0

    print(portable_status)
    print(f"Project root: {project_root}")
    print(f"Python executable: {asr_status.python_executable}")
    print(f"Python from project .venv: {asr_status.is_project_venv}")
    print(f"Whisper package path: {asr_status.whisper_package_path or 'MISSING'}")
    print(f"Whisper model dir: {asr_status.whisper_model_dir}")
    print(f"Whisper model files found: {asr_status.whisper_model_files_found}")
    print(f"Qwen mode: {provider}")
    print(f"Qwen model dir/state: {qwen_state}")
    print(f"ffmpeg path: {asr_status.ffmpeg_path or 'MISSING'}")
    print("C 盘缓存提示：仅检测路径，不处理源缓存。")
    for warning in warnings:
        print(f"WARN: {warning}")
    for issue in issues:
        print(f"FAIL: {issue}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
