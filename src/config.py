from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _fallback_yaml_parse(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        key, sep, value = stripped.partition(":")
        if sep == "":
            continue
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() == "":
            node: dict[str, Any] = {}
            parent[key.strip()] = node
            stack.append((indent, node))
        else:
            parent[key.strip()] = _parse_scalar(value)
    return root


def load_yaml(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"Missing config file: {target}")
    text = target.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Config must be a mapping: {target}")
        return data
    except ModuleNotFoundError:
        return _fallback_yaml_parse(text)


def write_yaml(path: str | Path, data: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml  # type: ignore

        target.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return
    except ModuleNotFoundError:
        pass
    target.write_text(_dump_fallback_yaml(data), encoding="utf-8")


def _dump_fallback_yaml(data: dict[str, Any], indent: int = 0) -> str:
    lines: list[str] = []
    prefix = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_dump_fallback_yaml(value, indent + 2).rstrip())
        elif isinstance(value, bool):
            lines.append(f"{prefix}{key}: {'true' if value else 'false'}")
        elif value is None:
            lines.append(f"{prefix}{key}: null")
        elif isinstance(value, (int, float)):
            lines.append(f"{prefix}{key}: {value}")
        else:
            lines.append(f"{prefix}{key}: {value!r}")
    return "\n".join(lines) + "\n"


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    return _deep_merge(base, overlay)


@dataclass(frozen=True)
class ConfigSet:
    app: dict[str, Any]
    models: dict[str, Any]
    go2: dict[str, Any]
    commands: dict[str, Any]
    go2_actions: dict[str, Any]
    safety: dict[str, Any]
    anbangtu: dict[str, Any]
    user_settings: dict[str, Any]
    config_dir: Path

    @classmethod
    def load(cls, config_dir: str | Path | None = None) -> "ConfigSet":
        base = Path(config_dir) if config_dir else project_root() / "configs"
        required = [
            "app.yaml",
            "models.yaml",
            "go2.yaml",
            "commands.yaml",
            "safety.yaml",
            "anbangtu.yaml",
        ]
        missing = [name for name in required if not (base / name).exists()]
        if missing:
            raise FileNotFoundError(
                f"Missing config file(s) in {base}: {', '.join(missing)}"
            )
        app = load_yaml(base / "app.yaml")
        user_settings_path = base / "user_settings.yaml"
        user_settings = load_yaml(user_settings_path) if user_settings_path.exists() else {}
        action_catalog_path = base / "go2_action_catalog.yaml"
        go2_actions = load_yaml(action_catalog_path) if action_catalog_path.exists() else {"actions": {}}
        merged_app = _deep_merge(app, user_settings)
        return cls(
            app=merged_app,
            models=load_yaml(base / "models.yaml"),
            go2=load_yaml(base / "go2.yaml"),
            commands=load_yaml(base / "commands.yaml"),
            go2_actions=go2_actions,
            safety=load_yaml(base / "safety.yaml"),
            anbangtu=load_yaml(base / "anbangtu.yaml"),
            user_settings=user_settings,
            config_dir=base,
        )

    @property
    def robot_mode(self) -> str:
        return str(self.app.get("robot_mode") or self.go2.get("robot_mode") or "mock")

    @property
    def enable_real_robot(self) -> bool:
        return bool(
            self.app.get("enable_real_robot", False)
            and self.go2.get("enable_real_robot", False)
        )

    @property
    def log_dir(self) -> Path:
        log_dir = Path(str(self.app.get("log_dir", "runtime_data/logs")))
        if not log_dir.is_absolute():
            log_dir = project_root() / log_dir
        return log_dir
