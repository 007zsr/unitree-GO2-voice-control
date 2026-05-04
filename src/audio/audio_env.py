from __future__ import annotations

import importlib
from dataclasses import asdict, dataclass, field
from typing import Any, Callable


WINDOWS_AUDIO_INSTALL = "python -m pip install sounddevice soundfile"
UBUNTU_AUDIO_INSTALL = (
    "sudo apt update && sudo apt install -y portaudio19-dev libsndfile1 && "
    "python3 -m pip install sounddevice soundfile"
)


@dataclass(frozen=True)
class AudioDependencyStatus:
    available: bool
    missing_packages: list[str] = field(default_factory=list)
    message: str = ""
    install_hint: str = WINDOWS_AUDIO_INSTALL
    ubuntu_hint: str = UBUNTU_AUDIO_INSTALL
    microphone_available: bool | None = None
    microphone_devices: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def user_message(self) -> str:
        if self.available:
            if self.microphone_available is False:
                return "音频依赖已安装，但未检测到可用麦克风输入设备。"
            return "音频采集依赖可用。"
        missing = ", ".join(self.missing_packages) or "sounddevice, soundfile"
        return (
            f"音频采集不可用：缺少 {missing}。\n"
            f"Windows 安装：{self.install_hint}\n"
            "Ubuntu 如仍失败，请安装 PortAudio/libsndfile："
            f"{self.ubuntu_hint}"
        )


class AudioDependencyError(RuntimeError):
    def __init__(self, status: AudioDependencyStatus):
        super().__init__(status.user_message())
        self.status = status


ImportModule = Callable[[str], Any]


def check_audio_dependencies(
    import_module: ImportModule | None = None,
    query_devices: bool = False,
) -> AudioDependencyStatus:
    importer = import_module or importlib.import_module
    missing: list[str] = []
    errors: list[str] = []
    modules: dict[str, Any] = {}

    for package in ["sounddevice", "soundfile"]:
        try:
            modules[package] = importer(package)
        except ModuleNotFoundError:
            missing.append(package)
        except Exception as exc:
            missing.append(package)
            errors.append(f"{package}: {exc.__class__.__name__}: {exc}")

    if missing:
        return AudioDependencyStatus(
            available=False,
            missing_packages=missing,
            message=f"音频采集不可用：缺少 {', '.join(missing)}",
            errors=errors,
        )

    microphone_available: bool | None = None
    microphone_devices: list[str] = []
    if query_devices:
        try:
            sounddevice = modules["sounddevice"]
            devices = sounddevice.query_devices()
            for device in devices:
                if isinstance(device, dict) and int(device.get("max_input_channels", 0)) > 0:
                    microphone_devices.append(str(device.get("name", "unknown input device")))
            microphone_available = bool(microphone_devices)
            if not microphone_available:
                errors.append("No microphone input devices reported by sounddevice")
        except Exception as exc:
            microphone_available = False
            errors.append(f"microphone query failed: {exc.__class__.__name__}: {exc}")

    return AudioDependencyStatus(
        available=True,
        message="音频采集依赖可用",
        microphone_available=microphone_available,
        microphone_devices=microphone_devices,
        errors=errors,
    )
