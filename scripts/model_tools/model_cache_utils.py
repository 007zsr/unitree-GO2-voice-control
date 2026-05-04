from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


WHISPER_MODEL_NAMES = {
    "tiny.pt",
    "tiny.en.pt",
    "base.pt",
    "base.en.pt",
    "small.pt",
    "small.en.pt",
    "medium.pt",
    "medium.en.pt",
    "large.pt",
    "large-v1.pt",
    "large-v2.pt",
    "large-v3.pt",
    "turbo.pt",
}
TOKENIZER_NAMES = {"tokenizer.json", "tokenizer_config.json"}
WEIGHT_SUFFIXES = {".safetensors", ".bin"}


@dataclass(frozen=True)
class FileCandidate:
    path: Path
    size: int
    sha256: str = ""

    def to_dict(self) -> dict[str, object]:
        return {"path": str(self.path), "size": self.size, "sha256": self.sha256}


@dataclass(frozen=True)
class DirectoryCandidate:
    path: Path
    name: str
    weight_files: list[str]
    tokenizer_files: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "name": self.name,
            "weight_files": self.weight_files,
            "tokenizer_files": self.tokenizer_files,
        }


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def common_cache_roots() -> dict[str, Path]:
    home = Path.home()
    cache = home / ".cache"
    return {
        "whisper": cache / "whisper",
        "torch": cache / "torch",
        "huggingface": cache / "huggingface",
        "modelscope": cache / "modelscope",
    }


def existing_cache_roots() -> dict[str, Path]:
    return {name: path for name, path in common_cache_roots().items() if path.exists()}


def _within_depth(root: Path, target: Path, max_depth: int) -> bool:
    try:
        relative = target.relative_to(root)
    except ValueError:
        return False
    return len(relative.parts) <= max_depth


def _iter_files(root: Path, max_depth: int):
    if not root.exists():
        return
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_dir():
                if _within_depth(root, child, max_depth):
                    stack.append(child)
            elif child.is_file():
                yield child


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_whisper_candidates(with_hash: bool = False) -> tuple[list[Path], list[FileCandidate], list[dict[str, str]]]:
    roots = common_cache_roots()
    scan_roots = [roots["whisper"], roots["torch"]]
    candidates: list[FileCandidate] = []
    skipped: list[dict[str, str]] = []
    scanned = [root for root in scan_roots if root.exists()]
    for root in scanned:
        max_depth = 3 if root.name == "whisper" else 6
        for path in _iter_files(root, max_depth=max_depth):
            if path.name in WHISPER_MODEL_NAMES:
                size = path.stat().st_size
                candidates.append(
                    FileCandidate(
                        path=path,
                        size=size,
                        sha256=sha256_file(path) if with_hash else "",
                    )
                )
            elif path.suffix == ".pt":
                skipped.append({"path": str(path), "reason": "pt 文件名不是已知 Whisper 模型名"})
    return scanned, candidates, skipped


def _read_json(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _is_qwen_config(config_path: Path) -> bool:
    text_hint = str(config_path).lower()
    if "qwen" in text_hint:
        return True
    data = _read_json(config_path)
    values = " ".join(str(value).lower() for value in data.values())
    return "qwen" in values


def _qwen_candidate_from_dir(directory: Path) -> DirectoryCandidate | None:
    config_path = directory / "config.json"
    if not config_path.exists() or not _is_qwen_config(config_path):
        return None
    tokenizer_files = [
        item.name
        for item in directory.iterdir()
        if item.is_file() and item.name in TOKENIZER_NAMES
    ]
    weight_files = [
        item.name
        for item in directory.iterdir()
        if item.is_file() and item.suffix in WEIGHT_SUFFIXES
    ]
    if not tokenizer_files or not weight_files:
        return None
    return DirectoryCandidate(
        path=directory,
        name=_qwen_model_name(directory),
        weight_files=sorted(weight_files),
        tokenizer_files=sorted(tokenizer_files),
    )


def _qwen_model_name(directory: Path) -> str:
    parts = directory.parts
    for part in reversed(parts):
        if "qwen" in part.lower():
            return part.replace("models--", "").replace("--", "_")
    return directory.name


def scan_qwen_candidates() -> tuple[list[Path], list[DirectoryCandidate], list[dict[str, str]]]:
    roots = common_cache_roots()
    scan_roots = [roots["huggingface"], roots["modelscope"]]
    candidates: list[DirectoryCandidate] = []
    skipped: list[dict[str, str]] = []
    scanned = [root for root in scan_roots if root.exists()]
    seen: set[Path] = set()
    for root in scanned:
        for path in _iter_files(root, max_depth=9):
            if path.name != "config.json":
                continue
            directory = path.parent
            if directory in seen:
                continue
            seen.add(directory)
            candidate = _qwen_candidate_from_dir(directory)
            if candidate is not None:
                candidates.append(candidate)
            elif "qwen" in str(directory).lower():
                skipped.append({"path": str(directory), "reason": "Qwen 线索存在，但目录结构不完整"})
    return scanned, candidates, skipped


def copy_file_candidate(candidate: FileCandidate, target_dir: Path) -> dict[str, object]:
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / candidate.path.name
    if target.exists():
        if target.stat().st_size == candidate.size:
            return {
                "source": str(candidate.path),
                "target": str(target),
                "status": "skipped_same_size",
                "size": candidate.size,
            }
        target = _variant_path(target)
    shutil.copy2(candidate.path, target)
    target_size = target.stat().st_size
    return {
        "source": str(candidate.path),
        "target": str(target),
        "status": "copied" if target_size == candidate.size else "copy_size_mismatch",
        "source_size": candidate.size,
        "target_size": target_size,
        "source_sha256": candidate.sha256,
        "target_sha256": sha256_file(target) if candidate.sha256 else "",
    }


def copy_qwen_candidate(candidate: DirectoryCandidate, target_root: Path) -> dict[str, object]:
    target_root.mkdir(parents=True, exist_ok=True)
    target = target_root / candidate.name
    if target.exists():
        target = _variant_path(target)
    shutil.copytree(candidate.path, target)
    core_files = ["config.json", *candidate.tokenizer_files]
    copied_core = [name for name in core_files if (target / name).exists()]
    copied_weights = [name for name in candidate.weight_files if (target / name).exists()]
    return {
        "source": str(candidate.path),
        "target": str(target),
        "status": "copied" if len(copied_core) == len(core_files) and copied_weights else "copy_incomplete",
        "core_files": copied_core,
        "weight_files": copied_weights,
    }


def _variant_path(path: Path) -> Path:
    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    for index in range(1, 1000):
        candidate = parent / f"{stem}_from_cache_{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Too many target variants for {path}")


def write_report(
    report_path: Path,
    scanned_dirs: list[Path],
    whisper_candidates: list[FileCandidate] | None = None,
    qwen_candidates: list[DirectoryCandidate] | None = None,
    copied_whisper: list[dict[str, object]] | None = None,
    copied_qwen: list[dict[str, object]] | None = None,
    skipped: list[dict[str, str]] | None = None,
) -> None:
    whisper_candidates = whisper_candidates or []
    qwen_candidates = qwen_candidates or []
    copied_whisper = copied_whisper or []
    copied_qwen = copied_qwen or []
    skipped = skipped or []
    lines = [
        "# Model Migration Report",
        "",
        f"扫描时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        "## 扫描目录",
    ]
    lines.extend([f"- {path}" for path in scanned_dirs] or ["- 未找到常见缓存目录"])
    lines.extend(["", "## 发现的 Whisper 候选文件"])
    lines.extend(
        [f"- {item.path} ({item.size} bytes)" for item in whisper_candidates]
        or ["- 未找到可确认的 Whisper 模型文件"]
    )
    lines.extend(["", "## 已复制的 Whisper 文件"])
    lines.extend(
        [
            f"- {item.get('status')}: {item.get('source')} -> {item.get('target')}"
            for item in copied_whisper
        ]
        or ["- 无"]
    )
    lines.extend(["", "## 发现的 Qwen 候选目录"])
    lines.extend(
        [f"- {item.path}" for item in qwen_candidates]
        or ["- 未找到可确认的 Qwen 本地模型目录"]
    )
    lines.extend(["", "## 已复制的 Qwen 目录"])
    lines.extend(
        [f"- {item.get('status')}: {item.get('source')} -> {item.get('target')}" for item in copied_qwen]
        or ["- 无"]
    )
    lines.extend(["", "## 跳过的文件 / 目录"])
    lines.extend([f"- {item.get('path')}: {item.get('reason')}" for item in skipped] or ["- 无"])
    lines.extend(
        [
            "",
            "## 源文件处理",
            "",
            "源文件仍保留在原位置，未删除。",
            "如需清理 C 盘缓存，请用户手动确认后自行处理。",
            "",
            "## 后续建议",
            "",
            "- 使用 project_cli.py portable-check 或 scripts/check/check_portable_project.py 检查项目便携状态。",
            "- GitHub 默认不要提交 .venv 或大型模型权重。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
