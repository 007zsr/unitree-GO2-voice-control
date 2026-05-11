from __future__ import annotations

from pathlib import Path

import _bootstrap  # noqa: F401
from src.asr.asr_env import check_asr_dependencies, is_project_venv_python, resolve_project_path
from src.config import ConfigSet
from src.nlu.local_qwen_provider import check_local_qwen_model
from src.nlu.semantic_engine_config import semantic_engine_config


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
    semantic_config = semantic_engine_config(configs.app, configs.models)
    whisper_model_dir = resolve_project_path(
        str(asr_config.get("download_root") or asr_config.get("model_dir") or "models/whisper"),
        project_root,
    )
    qwen_model_dir = resolve_project_path(str(semantic_config.get("local_llm_model_dir") or "models/qwen"), project_root)
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
    provider = str(semantic_config.get("llm_provider") or "local_qwen")
    semantic_mode = str(semantic_config.get("mode") or "traditional")
    qwen_status = check_local_qwen_model(qwen_model_dir, project_root)
    qwen_state = str(qwen_model_dir)
    if provider == "local_qwen":
        if not _inside(str(qwen_model_dir), project_root / "models" / "qwen"):
            warnings.append("Qwen local model directory is not under models/qwen")
        if semantic_mode == "llm_fallback" and bool(semantic_config.get("llm_enabled")) and not qwen_status.available:
            warnings.append(f"Qwen fallback enabled but local model is unavailable: {qwen_status.reason}")
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
    print(f"Semantic engine mode: {semantic_mode}")
    print(f"LLM enabled: {bool(semantic_config.get('llm_enabled'))}")
    print(f"LLM provider: {provider}")
    print(f"Qwen model dir/state: {qwen_state}")
    print(f"Qwen available: {qwen_status.available}")
    print(f"Qwen status reason: {qwen_status.reason}")
    print(f"Qwen tokenizer files: {', '.join(qwen_status.tokenizer_files) or 'MISSING'}")
    print(f"Qwen weight files: {', '.join(qwen_status.weight_files) or 'MISSING'}")
    print(f"Transformers available: {qwen_status.transformers_available}")
    print(f"Torch available: {qwen_status.torch_available}")
    print(f"ffmpeg path: {asr_status.ffmpeg_path or 'MISSING'}")
    print("C 盘缓存提示：仅检测路径，不处理源缓存。")
    for warning in warnings:
        print(f"WARN: {warning}")
    for issue in issues:
        print(f"FAIL: {issue}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
