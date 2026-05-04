from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.runtime.session_runtime import SessionRuntime


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one text command demo")
    parser.add_argument("--text", default="向前走一秒")
    parser.add_argument("--config-dir", default=str(_bootstrap.PROJECT_ROOT / "configs"))
    args = parser.parse_args()

    runtime = SessionRuntime.from_config_dir(args.config_dir)
    runtime.start()
    try:
        result = runtime.process_text(args.text)
        print(result.to_pretty_json())
        runtime.wait_until_idle(timeout_sec=10)
        return 0 if result.accepted else 2
    finally:
        runtime.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
