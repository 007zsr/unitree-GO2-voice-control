from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import ConfigSet
from src.runtime.session_runtime import SessionRuntime


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe mock command sequence")
    parser.add_argument("--config-dir", default=str(_bootstrap.PROJECT_ROOT / "configs"))
    args = parser.parse_args()

    configs = ConfigSet.load(args.config_dir)
    configs.app["robot_mode"] = "mock"
    configs.app["enable_real_robot"] = False
    configs.go2["robot_mode"] = "mock"
    configs.go2["enable_real_robot"] = False

    runtime = SessionRuntime(configs)
    runtime.start()
    try:
        commands = ["站起来", "向前走一秒", "左转", "停下", "报告状态", "攻击他"]
        exit_code = 0
        for text in commands:
            result = runtime.process_text(text)
            print(f"\n>>> {text}")
            print(result.to_pretty_json())
            runtime.wait_until_idle(timeout_sec=5)
            if text != "攻击他" and not result.accepted:
                exit_code = 2
            if text == "攻击他" and result.accepted:
                exit_code = 3
        return exit_code
    finally:
        runtime.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
