from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from model_cache_utils import (
    copy_file_candidate,
    project_root,
    scan_qwen_candidates,
    scan_whisper_candidates,
    write_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy confirmed Whisper model files into models/whisper")
    parser.add_argument("--with-hash", action="store_true", help="Calculate SHA256 before and after copy")
    args = parser.parse_args()

    whisper_dirs, whisper_candidates, whisper_skipped = scan_whisper_candidates(with_hash=args.with_hash)
    qwen_dirs, qwen_candidates, qwen_skipped = scan_qwen_candidates()
    target_dir = project_root() / "models" / "whisper"
    copied = []

    print("Whisper model collection. Source files remain in place.")
    if not whisper_candidates:
        print("未找到可确认的 Whisper 模型文件")
    for candidate in whisper_candidates:
        print(f"Source: {candidate.path}")
        print(f"Target directory: {target_dir}")
        print(f"Size: {candidate.size} bytes")
        result = copy_file_candidate(candidate, target_dir)
        copied.append(result)
        print(f"Result: {result['status']} -> {result['target']}")

    report_path = project_root() / "docs" / "model_migration_report.md"
    write_report(
        report_path=report_path,
        scanned_dirs=[*whisper_dirs, *qwen_dirs],
        whisper_candidates=whisper_candidates,
        qwen_candidates=qwen_candidates,
        copied_whisper=copied,
        skipped=[*whisper_skipped, *qwen_skipped],
    )
    print("源文件仍保留在原位置，未删除。")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
