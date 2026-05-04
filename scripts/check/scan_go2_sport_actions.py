from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import importlib.util
from pathlib import Path
import re
import sys
import urllib.request
from typing import Any

import _bootstrap  # noqa: F401
from src.config import load_yaml, write_yaml


SPORT_CLIENT_URL = (
    "https://raw.githubusercontent.com/unitreerobotics/"
    "unitree_sdk2_python/master/unitree_sdk2py/go2/sport/sport_client.py"
)
SPORT_API_URL = (
    "https://raw.githubusercontent.com/unitreerobotics/"
    "unitree_sdk2_python/master/unitree_sdk2py/go2/sport/sport_api.py"
)


@dataclass
class SourceText:
    name: str
    path: str
    text: str


@dataclass
class SportActionRecord:
    official_name: str
    sdk_method: str = ""
    api_const: str = ""
    sdk_api_id: int | None = None
    parameters: list[str] = field(default_factory=list)
    registered: bool = False
    method_present: bool = False
    source_file: str = ""

    @property
    def intent(self) -> str:
        return _snake_case(self.official_name or self.sdk_method or self.api_const)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan Unitree Go2 SportClient high-level actions")
    parser.add_argument("--no-remote", action="store_true", help="Do not fall back to official GitHub raw files")
    args = parser.parse_args()

    project_root = _bootstrap.PROJECT_ROOT
    sources = _load_sources(project_root, allow_remote=not args.no_remote)
    records = parse_sport_sources(sources)
    if not records:
        print("No Go2 SportClient actions found.")
        return 2
    write_scan_outputs(project_root, records, sources)
    print(f"Found {len(records)} Go2 SportClient action(s).")
    print(f"Wrote {project_root / 'docs' / 'GO2_OFFICIAL_ACTION_SCAN.md'}")
    print(f"Wrote {project_root / 'configs' / 'go2_action_catalog.generated.yaml'}")
    supported_doc = write_supported_actions_doc(project_root)
    if supported_doc:
        print(f"Wrote {supported_doc}")
    return 0


def _load_sources(project_root: Path, allow_remote: bool) -> list[SourceText]:
    local = _find_local_sources(project_root)
    if local:
        return local
    if not allow_remote:
        return []
    return [
        SourceText("sport_client.py", SPORT_CLIENT_URL, _read_url(SPORT_CLIENT_URL)),
        SourceText("sport_api.py", SPORT_API_URL, _read_url(SPORT_API_URL)),
    ]


def _find_local_sources(project_root: Path) -> list[SourceText]:
    candidates: list[Path] = []
    for module_name in [
        "unitree_sdk2py.go2.sport.sport_client",
        "unitree_sdk2py.go2.sport.sport_api",
    ]:
        try:
            spec = importlib.util.find_spec(module_name)
        except (ImportError, AttributeError, ValueError):
            spec = None
        if spec and spec.origin:
            candidates.append(Path(spec.origin))
    for root in [project_root, project_root / ".venv"]:
        if not root.exists():
            continue
        candidates.extend(root.rglob("unitree_sdk2py/go2/sport/sport_client.py"))
        candidates.extend(root.rglob("unitree_sdk2py/go2/sport/sport_api.py"))
    sources = []
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        sources.append(SourceText(path.name, str(resolved), path.read_text(encoding="utf-8", errors="replace")))
    return sources


def _read_url(url: str) -> str:
    with urllib.request.urlopen(url, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_sport_sources(sources: list[SourceText]) -> list[SportActionRecord]:
    api_ids: dict[str, int] = {}
    registered: dict[str, SportActionRecord] = {}
    methods: dict[str, SportActionRecord] = {}
    for source in sources:
        if source.name == "sport_api.py" or "SPORT_API_ID_" in source.text:
            api_ids.update(_parse_api_ids(source.text))
        if source.name == "sport_client.py" or "_RegistApi" in source.text:
            for record in _parse_registered_actions(source):
                registered[record.api_const] = record
            for record in _parse_methods(source):
                methods[record.sdk_method] = record

    by_const: dict[str, SportActionRecord] = {}
    for api_const, record in registered.items():
        record.sdk_api_id = api_ids.get(api_const)
        by_const[api_const] = record
    for method in methods.values():
        method.sdk_api_id = api_ids.get(method.api_const)
        if method.api_const in by_const:
            target = by_const[method.api_const]
            target.sdk_method = method.sdk_method
            target.parameters = method.parameters
            target.method_present = True
            if not target.source_file:
                target.source_file = method.source_file
        else:
            by_const[method.api_const or method.sdk_method] = method

    return sorted(by_const.values(), key=lambda item: (item.sdk_api_id or 999999, item.official_name))


def _parse_api_ids(text: str) -> dict[str, int]:
    return {
        match.group(1): int(match.group(2))
        for match in re.finditer(r"\b(SPORT_API_ID_[A-Z0-9_]+)\s*=\s*(\d+)\b", text)
    }


def _parse_registered_actions(source: SourceText) -> list[SportActionRecord]:
    records: list[SportActionRecord] = []
    pattern = r"_RegistApi\((SPORT_API_ID_[A-Z0-9_]+),\s*0\)\s*#\s*([A-Za-z][A-Za-z0-9_]*)"
    for match in re.finditer(pattern, source.text):
        records.append(
            SportActionRecord(
                official_name=match.group(2),
                api_const=match.group(1),
                registered=True,
                source_file=source.path,
            )
        )
    return records


def _parse_methods(source: SourceText) -> list[SportActionRecord]:
    records: list[SportActionRecord] = []
    pattern = r"def\s+([A-Za-z_][A-Za-z0-9_]*)\(self(?P<args>[^)]*)\):(?P<body>.*?)(?=\s+def\s+[A-Za-z_][A-Za-z0-9_]*\(self|\Z)"
    for match in re.finditer(pattern, source.text, flags=re.DOTALL):
        method = match.group(1)
        if method in {"__init__", "Init"}:
            continue
        body = match.group("body")
        api_match = re.search(r"_Call(?:NoReply)?\((SPORT_API_ID_[A-Z0-9_]+)", body)
        records.append(
            SportActionRecord(
                official_name=method,
                sdk_method=method,
                api_const=api_match.group(1) if api_match else "",
                parameters=_parse_parameters(match.group("args")),
                method_present=True,
                source_file=source.path,
            )
        )
    return records


def _parse_parameters(args: str) -> list[str]:
    params: list[str] = []
    for raw in args.split(","):
        clean = raw.strip()
        if not clean:
            continue
        clean = clean.split(":", 1)[0].split("=", 1)[0].strip()
        if clean:
            params.append(clean)
    return params


def write_scan_outputs(project_root: Path, records: list[SportActionRecord], sources: list[SourceText]) -> None:
    docs_dir = project_root / "docs"
    configs_dir = project_root / "configs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    configs_dir.mkdir(parents=True, exist_ok=True)

    report = [
        "# Go2 Official SportClient Action Scan",
        "",
        "This report is generated by `project_cli.py scan-go2-actions`.",
        "",
        "## Sources",
        "",
    ]
    report.extend(f"- `{source.path}`" for source in sources)
    report.extend(["", "## Actions", ""])
    report.append("| API ID | Official Name | SDK Method | Parameters | Registered | Method Present |")
    report.append("| --- | --- | --- | --- | --- | --- |")
    for record in records:
        report.append(
            "| "
            + " | ".join(
                [
                    str(record.sdk_api_id or ""),
                    record.official_name,
                    record.sdk_method or "",
                    ", ".join(record.parameters),
                    "yes" if record.registered else "no",
                    "yes" if record.method_present else "no",
                ]
            )
            + " |"
        )
    (docs_dir / "GO2_OFFICIAL_ACTION_SCAN.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    generated: dict[str, Any] = {
        "generated_by": "scripts/check/scan_go2_sport_actions.py",
        "sources": [source.path for source in sources],
        "actions": {},
    }
    for record in records:
        generated["actions"][record.intent] = {
            "official_name": record.official_name,
            "sdk_method": record.sdk_method,
            "sdk_api_id": record.sdk_api_id,
            "official_supported": True,
            "risk_level": "disabled",
            "voice_enabled": False,
            "mock_enabled": True,
            "real_robot_enabled": False,
            "parameters": record.parameters,
            "registered": record.registered,
            "method_present": record.method_present,
            "source_file": record.source_file,
            "aliases": {"en": [], "zh": []},
            "reason": "Generated scan output only; review and copy into go2_action_catalog.yaml before enabling.",
        }
    write_yaml(configs_dir / "go2_action_catalog.generated.yaml", generated)


def write_supported_actions_doc(project_root: Path) -> Path | None:
    catalog_path = project_root / "configs" / "go2_action_catalog.yaml"
    if not catalog_path.exists():
        return None
    catalog = load_yaml(catalog_path)
    actions = catalog.get("actions", {})
    if not isinstance(actions, dict):
        return None
    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = {
        "safe": [],
        "caution": [],
        "dangerous": [],
        "disabled": [],
    }
    for intent, data in actions.items():
        if not isinstance(data, dict):
            continue
        risk = str(data.get("risk_level", "disabled")).lower()
        grouped.setdefault(risk, []).append((str(intent), data))

    lines = [
        "# Go2 Supported Actions and Voice Commands",
        "",
        "Generated from `configs/go2_action_catalog.yaml`.",
        "",
        "Official SDK support does not mean real-robot execution is enabled. Safety remains the final gate.",
        "",
    ]
    for risk in ["safe", "caution", "dangerous", "disabled"]:
        lines.extend([f"## {risk.title()}", ""])
        for intent, data in sorted(grouped.get(risk, [])):
            aliases = data.get("aliases", {}) if isinstance(data.get("aliases"), dict) else {}
            lines.extend(
                [
                    f"### {intent}",
                    "",
                    f"- Official SDK method: `{data.get('sdk_method') or data.get('official_name') or ''}`",
                    f"- Risk level: `{risk}`",
                    f"- English aliases: {', '.join(str(item) for item in aliases.get('en', [])) or '-'}",
                    f"- Chinese aliases: {', '.join(str(item) for item in aliases.get('zh', [])) or '-'}",
                    f"- Mock enabled: `{bool(data.get('mock_enabled', False))}`",
                    f"- Real robot enabled: `{bool(data.get('real_robot_enabled', False))}`",
                    f"- Requires standing: `{bool(data.get('requires_standing', False))}`",
                    f"- Reason: {data.get('reason') or data.get('description_en') or ''}",
                    "",
                ]
            )
    output_path = project_root / "docs" / "GO2_SUPPORTED_ACTIONS.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _snake_case(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.lower()


if __name__ == "__main__":
    raise SystemExit(main())
