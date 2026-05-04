from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from model_cache_utils import (
    project_root,
    scan_qwen_candidates,
    scan_whisper_candidates,
    write_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only scan for existing model caches")
    parser.add_argument("--with-hash", action="store_true", help="Calculate SHA256 for Whisper candidates")
    args = parser.parse_args()

    whisper_dirs, whisper_candidates, whisper_skipped = scan_whisper_candidates(with_hash=args.with_hash)
    qwen_dirs, qwen_candidates, qwen_skipped = scan_qwen_candidates()
    scanned_dirs = [*whisper_dirs, *qwen_dirs]
    skipped = [*whisper_skipped, *qwen_skipped]

    print("Read-only scan. No source files are changed.")
    print("Scanned directories:")
    for directory in scanned_dirs:
        print(f"  {directory}")
    if not scanned_dirs:
        print("  No common cache directories found.")

    print("\nWhisper candidates:")
    if whisper_candidates:
        for candidate in whisper_candidates:
            hash_text = f", sha256={candidate.sha256}" if candidate.sha256 else ""
            print(f"  {candidate.path} ({candidate.size} bytes{hash_text})")
    else:
        print("  未找到可确认的 Whisper 模型文件")

    print("\nQwen candidates:")
    if qwen_candidates:
        for candidate in qwen_candidates:
            print(f"  {candidate.path}")
    else:
        print("  未找到可确认的 Qwen 本地模型目录")

    print("\nSkipped:")
    if skipped:
        for item in skipped:
            print(f"  {item['path']}: {item['reason']}")
    else:
        print("  None")

    report_path = project_root() / "docs" / "model_migration_report.md"
    write_report(
        report_path=report_path,
        scanned_dirs=scanned_dirs,
        whisper_candidates=whisper_candidates,
        qwen_candidates=qwen_candidates,
        skipped=skipped,
    )
    print(f"\nReport: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
