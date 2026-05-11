from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config import project_root


SEMANTIC_ENGINE_DEFAULTS: dict[str, Any] = {
    "mode": "traditional",
    "llm_enabled": False,
    "llm_provider": "local_qwen",
    "llm_fallback_min_confidence": 0.60,
    "local_llm_model_dir": "models/qwen",
    "llm_timeout_seconds": 5.0,
    "llm_max_output_tokens": 128,
    "llm_temperature": 0.0,
    "llm_allow_remote_api": False,
}

SEMANTIC_ENGINE_MODES = {"traditional", "llm_fallback", "llm_only_debug"}
LLM_PROVIDERS = {
    "local_qwen",
    "openai_api_reserved",
    "custom_api_reserved",
    "disabled",
    "mock",
}

PROVIDER_ALIASES = {
    "mock_llm": "mock",
}

CONFIG_ALIASES = {
    "fallback_min_confidence": "llm_fallback_min_confidence",
    "local_model_dir": "local_llm_model_dir",
    "timeout_seconds": "llm_timeout_seconds",
    "max_output_tokens": "llm_max_output_tokens",
    "temperature": "llm_temperature",
    "allow_remote_api": "llm_allow_remote_api",
}


def semantic_engine_config(app_config: dict[str, Any], models_config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = dict(SEMANTIC_ENGINE_DEFAULTS)
    configured = app_config.get("semantic_engine", {})
    configured_keys: set[str] = set()
    if isinstance(configured, dict):
        normalized_configured = dict(configured)
        for alias, canonical in CONFIG_ALIASES.items():
            if alias in normalized_configured and canonical not in normalized_configured:
                normalized_configured[canonical] = normalized_configured[alias]
            normalized_configured.pop(alias, None)
        configured_keys = set(normalized_configured)
        config.update(normalized_configured)
    qwen = (models_config or {}).get("qwen", {}) if isinstance(models_config, dict) else {}
    if isinstance(qwen, dict):
        if not configured_keys or "local_llm_model_dir" not in configured_keys:
            config["local_llm_model_dir"] = qwen.get("local_model_dir") or config["local_llm_model_dir"]
        if not configured_keys or "llm_timeout_seconds" not in configured_keys:
            config["llm_timeout_seconds"] = qwen.get("timeout_sec") or config["llm_timeout_seconds"]
        if not configured_keys or "llm_temperature" not in configured_keys:
            config["llm_temperature"] = qwen.get("temperature", config["llm_temperature"])

    mode = str(config.get("mode") or "traditional").lower()
    invalid_mode = mode not in SEMANTIC_ENGINE_MODES
    if mode not in SEMANTIC_ENGINE_MODES:
        mode = "traditional"
    provider = str(config.get("llm_provider") or "local_qwen").lower()
    provider = PROVIDER_ALIASES.get(provider, provider)
    if provider not in LLM_PROVIDERS:
        provider = "disabled"
    config["mode"] = mode
    config["llm_provider"] = provider
    config["llm_enabled"] = False if invalid_mode else bool(config.get("llm_enabled", False))
    config["llm_fallback_min_confidence"] = float(config.get("llm_fallback_min_confidence", 0.60))
    config["llm_timeout_seconds"] = float(config.get("llm_timeout_seconds", 5.0))
    config["llm_max_output_tokens"] = int(config.get("llm_max_output_tokens", 128))
    config["llm_temperature"] = float(config.get("llm_temperature", 0.0))
    config["llm_allow_remote_api"] = bool(config.get("llm_allow_remote_api", False))
    config["local_llm_model_dir"] = str(config.get("local_llm_model_dir") or "models/qwen")
    return config


def resolve_model_dir(path_text: str | Path, root: Path | None = None) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return (root or project_root()) / path
