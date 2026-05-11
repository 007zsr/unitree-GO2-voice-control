from __future__ import annotations

import argparse
from pathlib import Path

from src.config import ConfigSet
from src.runtime.session_runtime import SessionRuntime
from src.runtime.runtime_overrides import apply_runtime_overrides, parse_allowed_actions


DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent / "configs"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unitree Go2 voice control entrypoint")
    parser.add_argument(
        "--gui",
        "--ui",
        action="store_true",
        dest="gui",
        help="Open the desktop UI. This is also the default when no text/audio command is provided.",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Use the original command-line prompt mode when no --text or --audio is provided.",
    )
    parser.add_argument(
        "--text",
        help="Run one text command through NLU, normalization, safety, and robot adapter.",
    )
    parser.add_argument(
        "--audio",
        help="Run one audio file through Whisper, NLU, normalization, safety, and robot adapter.",
    )
    parser.add_argument(
        "--config-dir",
        default=str(DEFAULT_CONFIG_DIR),
        help="Directory containing app.yaml, models.yaml, go2.yaml, commands.yaml, safety.yaml.",
    )
    parser.add_argument("--robot-mode", choices=["mock", "go2"], default="")
    parser.add_argument("--enable-real-robot", action="store_true")
    parser.add_argument("--interface", default="")
    parser.add_argument("--robot-ip", default="")
    parser.add_argument("--real-demo", action="store_true")
    parser.add_argument("--allowed-real-actions", default="")
    return parser


def run_gui(config_dir: str, runtime_overrides: dict[str, object] | None = None) -> int:
    try:
        from src.gui.app_window import Go2VoiceControlWindow
    except ModuleNotFoundError as exc:
        print(f"Missing GUI dependency: {exc}")
        print("tkinter is required. On Ubuntu install: sudo apt install python3-tk")
        return 2

    window = Go2VoiceControlWindow(config_dir=config_dir, runtime_overrides=runtime_overrides)
    window.mainloop()
    return 0


def run_command(args: argparse.Namespace) -> int:
    configs = ConfigSet.load(args.config_dir)
    apply_runtime_overrides(configs, runtime_overrides_from_args(args))
    runtime = SessionRuntime(configs)
    runtime.start()
    try:
        if args.audio:
            result = runtime.process_audio(args.audio)
        else:
            result = runtime.process_text(args.text or input("Command text: ").strip())
        print(result.to_pretty_json())
        runtime.wait_until_idle(timeout_sec=10.0)
        return 0 if result.accepted else 2
    finally:
        runtime.shutdown()


def main() -> int:
    args = build_parser().parse_args()
    should_open_gui = args.gui or (not args.cli and not args.text and not args.audio)
    if should_open_gui:
        return run_gui(args.config_dir, runtime_overrides_from_args(args))
    return run_command(args)


def runtime_overrides_from_args(args: argparse.Namespace) -> dict[str, object]:
    return {
        "robot_mode": args.robot_mode,
        "enable_real_robot": bool(args.enable_real_robot),
        "interface": args.interface,
        "robot_ip": args.robot_ip,
        "real_demo": bool(args.real_demo),
        "allowed_real_actions": parse_allowed_actions(args.allowed_real_actions),
    }


if __name__ == "__main__":
    raise SystemExit(main())
