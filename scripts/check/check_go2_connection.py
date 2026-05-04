from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import ConfigSet
from src.deployment.env_checker import EnvChecker, format_report
from src.robot.go2_adapter import Go2Adapter


def main() -> int:
    parser = argparse.ArgumentParser(description="Check real Unitree Go2 SDK connection")
    parser.add_argument("--config-dir", default=str(_bootstrap.PROJECT_ROOT / "configs"))
    parser.add_argument("--stop-test", action="store_true", help="Call StopMove after connection")
    args = parser.parse_args()

    configs = ConfigSet.load(args.config_dir)
    report = EnvChecker(configs).check_all()
    print(format_report(report))
    if configs.robot_mode != "go2" or not configs.enable_real_robot:
        print("Refusing real Go2 connection: set robot_mode=go2 and enable_real_robot=true in app.yaml and go2.yaml.")
        return 2
    failed = [item for item in report if item.status == "FAIL"]
    if failed:
        print("Refusing real Go2 connection because preflight has FAIL items.")
        return 3

    adapter = Go2Adapter(configs.go2)
    try:
        adapter.connect()
        state = adapter.get_state()
        print("Go2 connected. State:")
        print(state.to_dict())
        if args.stop_test:
            print(adapter.stop("connection_check").to_dict())
        return 0
    finally:
        adapter.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
