from __future__ import annotations

import importlib
import os
from pathlib import Path
import shutil
import sys
from dataclasses import asdict, dataclass
from typing import Any, Callable


WINDOWS_WHISPER_INSTALL = "python -m pip install -U openai-whisper"
UBUNTU_WHISPER_INSTALL = "python3 -m pip install -U openai-whisper"
WINDOWS_FFMPEG_WINGET_INSTALL = "winget install --id Gyan.FFmpeg -e"
WINDOWS_FFMPEG_CHOCO_INSTALL = "choco install ffmpeg"
UBUNTU_FFMPEG_INSTALL = "sudo apt update && sudo apt install -y ffmpeg"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_project_path(path_value: str | Path, root: str | Path | None = None) -> Path:
    root_path = Path(root).resolve() if root else project_root()
    target = Path(path_value)
    if not target.is_absolute():
        target = root_path / target
    return target.resolve()


def project_venv_dir(root: str | Path | None = None) -> Path:
    return resolve_project_path(".venv", root)


def is_project_venv_python(
    python_executable: str | Path | None = None,
    root: str | Path | None = None,
) -> bool:
    executable = Path(python_executable or sys.executable).resolve()
    venv_dir = project_venv_dir(root)
    try:
        executable.relative_to(venv_dir)
        return True
    except ValueError:
        return False


def resolve_whisper_model_dir(
    config: dict[str, Any] | None = None,
    root: str | Path | None = None,
) -> Path:
    config = config or {}
    download_root = (
        config.get("model_dir")
        or config.get("whisper_model_dir")
        or config.get("download_root")
        or config.get("whisper_download_root")
        or "models/whisper"
    )
    return resolve_project_path(str(download_root), root)


def _model_files(model_dir: Path) -> list[str]:
    if not model_dir.exists():
        return []
    return sorted(
        path.name
        for path in model_dir.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    )


@dataclass(frozen=True)
class AsrDependencyStatus:
    available: bool
    whisper_available: bool
    ffmpeg_available: bool
    python_executable: str
    python_version: str
    project_root: str = ""
    project_venv_path: str = ""
    is_project_venv: bool = False
    whisper_package_path: str = ""
    ffmpeg_path: str = ""
    model_name: str = ""
    whisper_model_dir: str = ""
    whisper_model_files_found: bool = False
    whisper_model_files: list[str] | None = None
    missing: list[str] | None = None
    missing_dependencies: list[str] | None = None
    message: str = ""
    install_hint: str = WINDOWS_WHISPER_INSTALL
    ubuntu_hint: str = UBUNTU_WHISPER_INSTALL
    ffmpeg_install_hint: str = WINDOWS_FFMPEG_WINGET_INSTALL
    ffmpeg_choco_hint: str = WINDOWS_FFMPEG_CHOCO_INSTALL
    ubuntu_ffmpeg_hint: str = UBUNTU_FFMPEG_INSTALL
    errors: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def whisper_installed(self) -> bool:
        return self.whisper_available

    def environment_message(self) -> str:
        env_text = "项目 .venv" if self.is_project_venv else "非项目环境"
        lines = [
            f"Python 环境：{env_text}",
            f"Python 路径：{self.python_executable}",
            f"Whisper 包路径：{self.whisper_package_path or '未找到'}",
            f"Whisper 模型目录：{self.whisper_model_dir or '未配置'}",
            f"ffmpeg：{'可用' if self.ffmpeg_available else '不可用'}"
            + (f" ({self.ffmpeg_path})" if self.ffmpeg_path else ""),
        ]
        if not self.is_project_venv:
            lines.append("警告：当前未使用项目 .venv，依赖可能来自系统 Python。")
        if self.whisper_available and not self.whisper_model_files_found:
            lines.append("Whisper 包已安装，但项目内模型目录暂无模型文件；首次运行会下载到该目录。")
        return "\n".join(lines)

    def user_message(self) -> str:
        if self.available:
            return f"ASR 可用：Whisper 已安装，ffmpeg 可用，模型配置为 {self.model_name or 'unknown'}。"

        missing = self.missing_dependencies or self.missing or []
        missing_text = " 和 ".join(missing) if len(missing) <= 2 else ", ".join(missing)
        lines = [f"ASR 不可用：缺少 {missing_text or 'openai-whisper / ffmpeg'}。"]
        lines.append(f"Whisper：{'OK' if self.whisper_available else '缺失'}")
        lines.append(f"ffmpeg：{'OK' if self.ffmpeg_available else '缺失'}")

        if not self.whisper_available and not self.ffmpeg_available:
            lines.append(f"请先安装 openai-whisper：{self.install_hint}")
            lines.append("然后安装 ffmpeg 并加入 PATH。")
            lines.append(f"Windows 可用 winget：{self.ffmpeg_install_hint}")
            lines.append(f"或 Chocolatey：{self.ffmpeg_choco_hint}")
            lines.append(f"Ubuntu：{self.ubuntu_ffmpeg_hint}")
            lines.append("安装后请重新打开终端和 GUI，并运行：ffmpeg -version")
        elif not self.whisper_available:
            lines.append("当前 Python 环境未安装 openai-whisper。")
            lines.append(f"请在运行 GUI 的同一个环境中执行：{self.install_hint}")
        elif not self.ffmpeg_available:
            lines.append("Whisper 已安装，但 ffmpeg 不可用，Whisper 无法可靠读取或转换音频。")
            lines.append("Windows 请安装 ffmpeg 并加入 PATH。")
            lines.append(f"推荐 winget：{self.ffmpeg_install_hint}")
            lines.append(f"也可使用 Chocolatey：{self.ffmpeg_choco_hint}")
            lines.append(f"Ubuntu：{self.ubuntu_ffmpeg_hint}")
            lines.append("安装后请重新打开终端和 GUI，并运行：ffmpeg -version")
        return "\n".join(lines)


ImportModule = Callable[[str], Any]
Which = Callable[[str], str | None]


def _read_windows_registry_path() -> str:
    if sys.platform != "win32":
        return ""
    try:
        import winreg
    except Exception:
        return ""

    values: list[str] = []
    registry_locations = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
        (winreg.HKEY_CURRENT_USER, "Environment"),
    ]
    for root, subkey in registry_locations:
        try:
            with winreg.OpenKey(root, subkey) as key:
                value, value_type = winreg.QueryValueEx(key, "Path")
        except OSError:
            continue
        if value_type == winreg.REG_EXPAND_SZ:
            value = os.path.expandvars(str(value))
        values.append(str(value))
    return os.pathsep.join(part for part in values if part)


def _refresh_windows_path_for_ffmpeg() -> str:
    latest_path = _read_windows_registry_path()
    if not latest_path:
        return ""
    ffmpeg_path = shutil.which("ffmpeg", path=latest_path) or ""
    if not ffmpeg_path:
        return ""
    current_parts = [part for part in os.environ.get("PATH", "").split(os.pathsep) if part]
    latest_parts = [part for part in latest_path.split(os.pathsep) if part]
    lower_current = {part.lower() for part in current_parts}
    missing_parts = [part for part in latest_parts if part.lower() not in lower_current]
    if missing_parts:
        os.environ["PATH"] = os.pathsep.join(current_parts + missing_parts)
    return ffmpeg_path


def check_asr_dependencies(
    model_name: str = "",
    model_dir: str | Path | None = None,
    project_root_path: str | Path | None = None,
    import_module: ImportModule | None = None,
    which: Which | None = None,
) -> AsrDependencyStatus:
    importer = import_module or importlib.import_module
    finder = which or shutil.which
    errors: list[str] = []
    missing: list[str] = []
    whisper_path = ""

    try:
        whisper_module = importer("whisper")
        whisper_path = str(getattr(whisper_module, "__file__", ""))
        whisper_available = True
    except ModuleNotFoundError:
        whisper_available = False
        missing.append("openai-whisper")
    except Exception as exc:
        whisper_available = False
        missing.append("openai-whisper")
        errors.append(f"whisper import failed: {exc.__class__.__name__}: {exc}")

    ffmpeg_path = finder("ffmpeg") or ""
    if not ffmpeg_path and which is None:
        ffmpeg_path = _refresh_windows_path_for_ffmpeg()
    ffmpeg_available = bool(ffmpeg_path)
    if not ffmpeg_available:
        missing.append("ffmpeg")

    root_path = Path(project_root_path).resolve() if project_root_path else project_root()
    resolved_model_dir = (
        resolve_project_path(model_dir, root_path)
        if model_dir
        else resolve_whisper_model_dir({"download_root": "models/whisper"}, root_path)
    )
    files = _model_files(resolved_model_dir)
    available = whisper_available and ffmpeg_available
    return AsrDependencyStatus(
        available=available,
        whisper_available=whisper_available,
        ffmpeg_available=ffmpeg_available,
        python_executable=sys.executable,
        python_version=sys.version.split()[0],
        project_root=str(root_path),
        project_venv_path=str(project_venv_dir(root_path)),
        is_project_venv=is_project_venv_python(sys.executable, root_path),
        whisper_package_path=whisper_path,
        ffmpeg_path=ffmpeg_path,
        model_name=model_name,
        whisper_model_dir=str(resolved_model_dir),
        whisper_model_files_found=bool(files),
        whisper_model_files=files,
        missing=missing,
        missing_dependencies=missing,
        message="ASR dependencies available" if available else "ASR dependencies missing",
        errors=errors,
    )
