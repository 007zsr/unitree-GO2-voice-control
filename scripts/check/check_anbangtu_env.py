from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from src.config import ConfigSet
from src.deployment.anbangtu_runtime import AnbangtuRuntime
from src.deployment.env_checker import EnvChecker, format_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check anbangtu deployment readiness")
    parser.add_argument("--config-dir", default=str(_bootstrap.PROJECT_ROOT / "configs"))
    args = parser.parse_args()

    configs = ConfigSet.load(args.config_dir)
    runtime = AnbangtuRuntime(configs.anbangtu)
    print("anbangtu runtime summary:")
    for key, value in runtime.summary().items():
        print(f"  {key}: {value}")
    print("\nenvironment report:")
    report = EnvChecker(configs).check_all()
    print(format_report(report))
    return 1 if any(item.status == "FAIL" for item in report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
