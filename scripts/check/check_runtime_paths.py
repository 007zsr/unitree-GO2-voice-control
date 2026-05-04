from __future__ import annotations

import importlib.util
import json
import shutil
import site
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
from src.asr.asr_env import (
    check_asr_dependencies,
    is_project_venv_python,
    project_venv_dir,
    resolve_whisper_model_dir,
)
from src.config import ConfigSet


def _package_path(package_name: str) -> str:
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return "MISSING"
    if spec.origin:
        return str(Path(spec.origin).resolve())
    locations = spec.submodule_search_locations
    if locations:
        return str(Path(next(iter(locations))).resolve())
    return "FOUND"


def _site_packages() -> list[str]:
    paths: list[str] = []
    try:
        paths.extend(site.getsitepackages())
    except Exception:
        pass
    try:
        paths.append(site.getusersitepackages())
    except Exception:
        pass
    return sorted(str(Path(path).resolve()) for path in paths if path)


def main() -> int:
    configs = ConfigSet.load(_bootstrap.PROJECT_ROOT / "configs")
    asr_config = configs.models.get("asr", {})
    model_dir = resolve_whisper_model_dir(asr_config if isinstance(asr_config, dict) else {})
    asr_status = check_asr_dependencies(
        model_name=str(asr_config.get("model_size", "base")) if isinstance(asr_config, dict) else "base",
        model_dir=model_dir,
    )
    project_root = _bootstrap.PROJECT_ROOT.resolve()
    project_venv = project_venv_dir(project_root)
    using_project_venv = is_project_venv_python(sys.executable, project_root)

    packages = {
        "whisper": _package_path("whisper"),
        "sounddevice": _package_path("sounddevice"),
        "soundfile": _package_path("soundfile"),
        "PySide6": _package_path("PySide6"),
    }
    result = {
        "project_root": str(project_root),
        "python_executable": sys.executable,
        "is_project_venv": using_project_venv,
        "project_venv": str(project_venv),
        "site_packages": _site_packages(),
        "packages": packages,
        "whisper_model_dir": str(model_dir),
        "ffmpeg_path": asr_status.ffmpeg_path or shutil.which("ffmpeg") or "MISSING",
        "sys_path": sys.path,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not using_project_venv:
        print("WARN: 当前没有使用项目 .venv。")
    whisper_path = packages["whisper"]
    if whisper_path != "MISSING" and not using_project_venv:
        print("WARN: Whisper 当前可能来自系统 Python 或用户 site-packages，不是项目 .venv。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
