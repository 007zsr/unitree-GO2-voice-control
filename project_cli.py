from __future__ import annotations

import csv
import platform
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON = Path(sys.executable)


SCRIPT_COMMANDS: dict[str, Path] = {
    "gui": Path("scripts/run/run_gui.py"),
    "asr-check": Path("scripts/check/check_asr_env.py"),
    "portable-check": Path("scripts/check/check_portable_project.py"),
    "audio-devices": Path("scripts/check/list_audio_devices.py"),
    "record-test": Path("scripts/test_tools/test_record_audio.py"),
    "whisper-test": Path("scripts/test_tools/test_whisper_file.py"),
    "go2-check": Path("scripts/check/check_go2_connection.py"),
    "logs": Path("scripts/check/show_recent_logs.py"),
    "scan-go2-actions": Path("scripts/check/scan_go2_sport_actions.py"),
    "fuzzy-text-test": Path("scripts/test_tools/run_fuzzy_text_batch.py"),
}


def _run_python(args: list[str]) -> int:
    print("Running:", " ".join([str(PYTHON), *args]), flush=True)
    completed = subprocess.run([str(PYTHON), *args], cwd=PROJECT_ROOT)
    return int(completed.returncode)


def _run_script(path: Path, extra_args: list[str] | None = None) -> int:
    script = PROJECT_ROOT / path
    if not script.exists():
        print(f"Missing script: {script}")
        return 2
    return _run_python([str(script), *(extra_args or [])])


def command_status(extra_args: list[str]) -> int:
    codes = [
        _run_script(Path("scripts/check/check_runtime_paths.py"), extra_args),
        _run_script(Path("scripts/check/check_portable_project.py"), []),
    ]
    return max(codes)


def command_test(extra_args: list[str]) -> int:
    return _run_python(["-m", "unittest", "discover", "-s", "tests", *extra_args])


def command_collect_models(extra_args: list[str]) -> int:
    with_hash = "--with-hash" in extra_args
    hash_args = ["--with-hash"] if with_hash else []
    print("Model collection is conservative: source cache files are never deleted.")
    codes = [
        _run_script(Path("scripts/model_tools/scan_existing_models_readonly.py"), hash_args),
        _run_script(Path("scripts/model_tools/collect_whisper_models.py"), hash_args),
        _run_script(Path("scripts/model_tools/collect_qwen_models.py"), []),
    ]
    return max(codes)


def command_audit(extra_args: list[str]) -> int:
    audit_dir = PROJECT_ROOT / "audits" / "project_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    files = [path for path in PROJECT_ROOT.rglob("*") if path.is_file()]
    root_items = list(PROJECT_ROOT.iterdir())

    (audit_dir / "root_items.txt").write_text(
        "\n".join(f"{item.name}\t{'dir' if item.is_dir() else item.stat().st_size}" for item in root_items),
        encoding="utf-8",
    )
    _write_files_csv(audit_dir / "all_files.csv", files)
    core_files = [
        path
        for path in files
        if ".venv" not in path.parts and "__pycache__" not in path.parts and ".git" not in path.parts
    ]
    _write_files_csv(audit_dir / "core_files_no_venv.csv", core_files)
    _write_directory_sizes(audit_dir / "top_level_directory_sizes.csv")
    _write_large_files(audit_dir / "large_files_over_10mb.csv", files)
    _write_filtered(audit_dir / "python_files.csv", core_files, lambda p: p.suffix == ".py")
    _write_filtered(
        audit_dir / "config_files.csv",
        core_files,
        lambda p: p.suffix.lower() in {".yaml", ".yml", ".json", ".toml", ".ini", ".env", ".example"},
    )
    _write_filtered(audit_dir / "script_files.csv", core_files, lambda p: p.suffix.lower() in {".bat", ".ps1", ".sh"})
    _write_filtered(audit_dir / "document_files.csv", core_files, lambda p: p.suffix.lower() in {".md", ".txt", ".rst"})
    _write_filtered(
        audit_dir / "model_related_files.csv",
        core_files,
        lambda p: "models" in p.parts or p.suffix.lower() in {".pt", ".pth", ".bin", ".safetensors", ".onnx", ".gguf", ".model"},
    )
    _write_filtered(
        audit_dir / "runtime_generated_files.csv",
        core_files,
        lambda p: "runtime_data" in p.parts or p.suffix.lower() in {".log", ".wav"},
    )
    _write_duplicate_names(audit_dir / "duplicate_file_names.csv", core_files)
    (audit_dir / "python_environment.txt").write_text(
        f"python={sys.executable}\nversion={sys.version}\nplatform={platform.platform()}\n",
        encoding="utf-8",
    )
    print(f"Audit written to: {audit_dir}")
    return 0


def _write_files_csv(path: Path, files: list[Path]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["FullName", "Length", "Extension", "LastWriteTime"])
        for file_path in sorted(files):
            stat = file_path.stat()
            writer.writerow([str(file_path), stat.st_size, file_path.suffix, stat.st_mtime])


def _write_directory_sizes(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Directory", "SizeMB", "FullName"])
        rows = []
        for directory in PROJECT_ROOT.iterdir():
            if not directory.is_dir():
                continue
            total = sum(child.stat().st_size for child in directory.rglob("*") if child.is_file())
            rows.append((directory.name, round(total / (1024 * 1024), 2), str(directory)))
        writer.writerows(sorted(rows, key=lambda row: row[1], reverse=True))


def _write_large_files(path: Path, files: list[Path]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["FullName", "SizeMB", "Extension", "LastWriteTime"])
        rows = []
        for file_path in files:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > 10:
                rows.append((str(file_path), round(size_mb, 2), file_path.suffix, file_path.stat().st_mtime))
        writer.writerows(sorted(rows, key=lambda row: row[1], reverse=True))


def _write_filtered(path: Path, files: list[Path], predicate) -> None:
    _write_files_csv(path, [file_path for file_path in files if predicate(file_path)])


def _write_duplicate_names(path: Path, files: list[Path]) -> None:
    groups: dict[str, list[Path]] = defaultdict(list)
    for file_path in files:
        groups[file_path.name].append(file_path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["FileName", "Count", "Paths"])
        for name, paths in sorted(groups.items()):
            if len(paths) > 1:
                writer.writerow([name, len(paths), " | ".join(str(path) for path in paths)])


def usage() -> None:
    commands = [
        "status",
        "gui",
        "test",
        "asr-check",
        "portable-check",
        "audio-devices",
        "record-test",
        "whisper-test",
        "collect-models",
        "go2-check",
        "audit",
        "logs",
        "scan-go2-actions",
        "fuzzy-text-test",
    ]
    print("Usage: python project_cli.py <command> [args...]")
    print("Commands:")
    for command in commands:
        print(f"  {command}")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        usage()
        return 0
    command = args[0]
    extra_args = args[1:]

    if command == "status":
        return command_status(extra_args)
    if command == "test":
        return command_test(extra_args)
    if command == "collect-models":
        return command_collect_models(extra_args)
    if command == "audit":
        return command_audit(extra_args)
    if command == "go2-check":
        print("Go2 check is connection/status oriented. It does not issue motion commands by default.", flush=True)
        return _run_script(SCRIPT_COMMANDS[command], extra_args)
    if command == "whisper-test" and not extra_args:
        default_audio = PROJECT_ROOT / "runtime_data" / "debug_audio" / "last_record.wav"
        if default_audio.exists():
            extra_args = ["--audio", str(default_audio)]
    if command in SCRIPT_COMMANDS:
        return _run_script(SCRIPT_COMMANDS[command], extra_args)

    print(f"Unknown command: {command}")
    usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
