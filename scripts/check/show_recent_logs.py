from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401
from src.config import ConfigSet


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    records: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Show recent structured pipeline logs")
    parser.add_argument("--last", type=int, default=10, help="Number of index rows to show")
    parser.add_argument("--errors", action="store_true", help="Show recent error records instead of the index")
    args = parser.parse_args()

    configs = ConfigSet.load(_bootstrap.PROJECT_ROOT / "configs")
    logging_config = configs.app.get("logging", {})
    root_dir = Path(str(logging_config.get("root_dir") or configs.app.get("log_dir", "runtime_data/logs")))
    if not root_dir.is_absolute():
        root_dir = _bootstrap.PROJECT_ROOT / root_dir

    if args.errors:
        error_files = sorted((root_dir / "errors").glob("*.jsonl"), reverse=True)
        records: list[dict[str, object]] = []
        for error_file in error_files:
            records.extend(_read_jsonl(error_file))
            if len(records) >= args.last:
                break
        print(f"Recent errors from: {root_dir / 'errors'}")
    else:
        records = _read_jsonl(root_dir / "index" / "log_index.jsonl")
        print(f"Recent logs from: {root_dir / 'index' / 'log_index.jsonl'}")

    for record in records[-args.last:]:
        timestamp = record.get("timestamp", "")
        mode = record.get("mode", "")
        status = record.get("status", "")
        command_id = record.get("command_id", "")
        listen_id = record.get("listen_id", "")
        path = record.get("log_path", "")
        summary = record.get("summary") or record.get("message", "")
        print(f"{timestamp} | {mode} | {status} | {command_id or listen_id} | {path} | {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
