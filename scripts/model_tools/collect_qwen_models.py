from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from model_cache_utils import (
    copy_qwen_candidate,
    project_root,
    scan_qwen_candidates,
    scan_whisper_candidates,
    write_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy confirmed Qwen model directories into models/qwen")
    parser.parse_args()

    whisper_dirs, whisper_candidates, whisper_skipped = scan_whisper_candidates(with_hash=False)
    qwen_dirs, qwen_candidates, qwen_skipped = scan_qwen_candidates()
    target_root = project_root() / "models" / "qwen"
    copied = []

    print("Qwen model collection. Source directories remain in place.")
    if not qwen_candidates:
        print("未找到可确认的 Qwen 本地模型目录")
    for candidate in qwen_candidates:
        print(f"Source: {candidate.path}")
        print(f"Target root: {target_root}")
        print(f"Tokenizer files: {', '.join(candidate.tokenizer_files)}")
        print(f"Weight files: {', '.join(candidate.weight_files)}")
        result = copy_qwen_candidate(candidate, target_root)
        copied.append(result)
        print(f"Result: {result['status']} -> {result['target']}")

    report_path = project_root() / "docs" / "model_migration_report.md"
    write_report(
        report_path=report_path,
        scanned_dirs=[*whisper_dirs, *qwen_dirs],
        whisper_candidates=whisper_candidates,
        qwen_candidates=qwen_candidates,
        copied_qwen=copied,
        skipped=[*whisper_skipped, *qwen_skipped],
    )
    print("源目录仍保留在原位置，未删除。")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
