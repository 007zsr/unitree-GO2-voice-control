from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from main import run_gui


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Go2 voice control desktop GUI")
    parser.add_argument("--config-dir", default=str(_bootstrap.PROJECT_ROOT / "configs"))
    args = parser.parse_args()

    return run_gui(args.config_dir)


if __name__ == "__main__":
    raise SystemExit(main())
