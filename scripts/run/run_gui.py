from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from main import run_gui
from src.runtime.runtime_overrides import parse_allowed_actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Go2 voice control desktop GUI")
    parser.add_argument("--config-dir", default=str(_bootstrap.PROJECT_ROOT / "configs"))
    parser.add_argument("--robot-mode", choices=["mock", "go2"], default="")
    parser.add_argument("--enable-real-robot", action="store_true")
    parser.add_argument("--interface", default="")
    parser.add_argument("--robot-ip", default="")
    parser.add_argument("--real-demo", action="store_true")
    parser.add_argument("--allowed-real-actions", default="")
    args = parser.parse_args()

    return run_gui(
        args.config_dir,
        {
            "robot_mode": args.robot_mode,
            "enable_real_robot": bool(args.enable_real_robot),
            "interface": args.interface,
            "robot_ip": args.robot_ip,
            "real_demo": bool(args.real_demo),
            "allowed_real_actions": parse_allowed_actions(args.allowed_real_actions),
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
