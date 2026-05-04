from __future__ import annotations

import importlib.util
import os
import platform
import socket
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from src.asr.asr_env import check_asr_dependencies, resolve_whisper_model_dir
from src.audio.audio_env import check_audio_dependencies
from src.config import ConfigSet


@dataclass(frozen=True)
class CheckItem:
    name: str
    status: str
    message: str
    details: dict[str, Any] | None = None


class EnvChecker:
    def __init__(self, configs: ConfigSet):
        self.configs = configs

    def check_all(self) -> list[CheckItem]:
        return [
            self.check_os(),
            self.check_python_version(),
            self.check_robot_mode(),
            self.check_unitree_sdk(),
            self.check_cyclonedds(),
            self.check_network_interface(),
            self.check_go2_network_access(),
            self.check_audio_dependencies(),
            self.check_microphone_device(),
            self.check_asr_dependencies(),
            self.check_gpu(),
            self.check_background_capability(),
        ]

    def check_os(self) -> CheckItem:
        return CheckItem(
            "os",
            "PASS",
            f"{platform.system()} {platform.release()}",
            {"platform": platform.platform()},
        )

    def check_python_version(self) -> CheckItem:
        min_version = str(self.configs.anbangtu.get("python_min_version", "3.8"))
        required = tuple(int(part) for part in min_version.split(".")[:2])
        current = sys.version_info[:2]
        status = "PASS" if current >= required else "FAIL"
        return CheckItem(
            "python_version",
            status,
            f"Python {sys.version.split()[0]}, required >= {min_version}",
        )

    def check_robot_mode(self) -> CheckItem:
        mode = self.configs.robot_mode
        if mode == "mock":
            return CheckItem("robot_mode", "PASS", "mock mode; real robot is disabled")
        if mode == "go2" and self.configs.enable_real_robot:
            return CheckItem("robot_mode", "PASS", "go2 mode with enable_real_robot=true")
        return CheckItem(
            "robot_mode",
            "FAIL",
            "go2 mode requires both app.yaml and go2.yaml enable_real_robot=true",
        )

    def check_unitree_sdk(self) -> CheckItem:
        found = importlib.util.find_spec("unitree_sdk2py") is not None
        if found:
            return CheckItem("unitree_sdk2_python", "PASS", "unitree_sdk2py import spec found")
        status = "FAIL" if self.configs.robot_mode == "go2" else "WARN"
        return CheckItem(
            "unitree_sdk2_python",
            status,
            "unitree_sdk2py is not installed; real Go2 control is unavailable",
        )

    def check_cyclonedds(self) -> CheckItem:
        found = importlib.util.find_spec("cyclonedds") is not None
        env_hint = bool(os.getenv("CYCLONEDDS_HOME") or os.getenv("CMAKE_PREFIX_PATH"))
        if found:
            return CheckItem(
                "cyclonedds",
                "PASS",
                "cyclonedds Python module found",
                {"env_hint": env_hint},
            )
        status = "FAIL" if self.configs.robot_mode == "go2" else "WARN"
        return CheckItem(
            "cyclonedds",
            status,
            "CycloneDDS is not available; Unitree SDK communication may fail",
            {"env_hint": env_hint},
        )

    def check_network_interface(self) -> CheckItem:
        interface = str(self.configs.go2.get("network_interface") or "").strip()
        interfaces = self._network_interfaces()
        if not interface:
            status = "FAIL" if self.configs.robot_mode == "go2" else "WARN"
            return CheckItem(
                "network_interface",
                status,
                "network_interface is not configured",
                {"interfaces": interfaces},
            )
        if interface in interfaces:
            return CheckItem(
                "network_interface",
                "PASS",
                f"network interface {interface!r} found",
                {"interfaces": interfaces},
            )
        status = "FAIL" if self.configs.robot_mode == "go2" else "WARN"
        return CheckItem(
            "network_interface",
            status,
            f"network interface {interface!r} was not found",
            {"interfaces": interfaces},
        )

    def check_go2_network_access(self) -> CheckItem:
        robot_ip = str(self.configs.go2.get("robot_ip") or "").strip()
        if not robot_ip:
            return CheckItem("go2_network", "WARN", "robot_ip is not configured; ping skipped")
        cmd = ["ping", "-n" if platform.system().lower() == "windows" else "-c", "1", robot_ip]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        except Exception as exc:
            status = "FAIL" if self.configs.robot_mode == "go2" else "WARN"
            return CheckItem("go2_network", status, f"ping failed to run: {exc}")
        status = "PASS" if result.returncode == 0 else ("FAIL" if self.configs.robot_mode == "go2" else "WARN")
        return CheckItem(
            "go2_network",
            status,
            f"ping {robot_ip} exit code {result.returncode}",
        )

    def check_audio_dependencies(self) -> CheckItem:
        status = check_audio_dependencies(query_devices=False)
        if status.available:
            return CheckItem(
                "audio_dependencies",
                "PASS",
                "sounddevice and soundfile are available",
                status.to_dict(),
            )

        audio_config = self.configs.app.get("audio", {})
        voice_required = bool(audio_config.get("require_microphone", False))
        item_status = "FAIL" if voice_required else "WARN"
        return CheckItem(
            "audio_dependencies",
            item_status,
            (
                "audio dependencies missing; text/mock control still works, "
                "GUI voice listening is unavailable"
            ),
            {
                **status.to_dict(),
                "mock_text_mode": "WARN: unaffected; one-shot text still works",
                "gui_voice_mode": "FAIL: start listening and one-shot voice are unavailable",
                "go2_text_mode": "WARN: text control can still run if Go2 preflight passes",
                "go2_voice_mode": "FAIL: voice control requires audio dependencies",
            },
        )

    def check_microphone_device(self) -> CheckItem:
        status = check_audio_dependencies(query_devices=True)
        if not status.available:
            return CheckItem(
                "microphone_device",
                "WARN",
                "microphone device check skipped because audio dependencies are missing",
                status.to_dict(),
            )
        if status.microphone_available:
            return CheckItem(
                "microphone_device",
                "PASS",
                f"{len(status.microphone_devices)} microphone input device(s) found",
                {"devices": status.microphone_devices},
            )
        return CheckItem(
            "microphone_device",
            "WARN",
            "no microphone input device detected; text mode still works",
            status.to_dict(),
        )

    def check_asr_dependencies(self) -> CheckItem:
        asr_config = self.configs.models.get("asr", {})
        model_name = str(asr_config.get("model_size", "base"))
        model_dir = resolve_whisper_model_dir(asr_config if isinstance(asr_config, dict) else {})
        status = check_asr_dependencies(model_name=model_name, model_dir=model_dir)
        if status.available:
            return CheckItem(
                "asr_dependencies",
                "PASS",
                "openai-whisper and ffmpeg are available",
                status.to_dict(),
            )

        asr_config = self.configs.models.get("asr", {})
        voice_required = bool(asr_config.get("require_asr", False))
        item_status = "FAIL" if voice_required else "WARN"
        missing_text = ", ".join(status.missing_dependencies or status.missing or []) or "unknown"
        return CheckItem(
            "asr_dependencies",
            item_status,
            (
                f"ASR dependencies missing ({missing_text}); text/mock control still works, "
                "GUI voice listening is unavailable"
            ),
            {
                **status.to_dict(),
                "fix_hint": status.user_message(),
                "mock_text_mode": "WARN: unaffected; one-shot text still works",
                "gui_voice_mode": "FAIL: start listening and one-shot voice are unavailable",
                "go2_text_mode": "WARN: text control can still run if Go2 preflight passes",
                "go2_voice_mode": "FAIL: voice control requires openai-whisper and ffmpeg",
            },
        )

    def check_gpu(self) -> CheckItem:
        try:
            import torch  # type: ignore

            available = bool(torch.cuda.is_available())
        except Exception:
            available = False
        required = bool(self.configs.anbangtu.get("gpu_required", False))
        if available:
            return CheckItem("gpu", "PASS", "CUDA GPU available")
        return CheckItem("gpu", "FAIL" if required else "WARN", "CUDA GPU not available")

    def check_background_capability(self) -> CheckItem:
        setting = self.configs.anbangtu.get("allow_background_process", "unknown")
        if setting is True:
            return CheckItem("background_process", "PASS", "background process allowed by config")
        if setting is False:
            return CheckItem("background_process", "FAIL", "background process disallowed by config")
        return CheckItem("background_process", "WARN", "background process permission is unknown")

    def _network_interfaces(self) -> list[str]:
        try:
            return [name for _, name in socket.if_nameindex()]
        except Exception:
            return []


def format_report(items: list[CheckItem]) -> str:
    lines = []
    for item in items:
        lines.append(f"[{item.status}] {item.name}: {item.message}")
        if item.details:
            lines.append(f"  details: {item.details}")
    return "\n".join(lines)
