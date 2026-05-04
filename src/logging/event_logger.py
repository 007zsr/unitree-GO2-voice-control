from __future__ import annotations

import json
import logging
import traceback
from pathlib import Path
from typing import Any

from src.models import utc_now_iso


class EventLogger:
    def __init__(self, log_dir: str | Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._loggers: dict[str, logging.Logger] = {}
        for name in ["asr", "nlu", "safety", "go2", "session"]:
            self._loggers[name] = self._build_logger(name)

    def _build_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(f"go2_voice_control.{name}.{id(self)}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if not logger.handlers:
            handler = logging.FileHandler(self.log_dir / f"{name}.log", encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
        return logger

    def log(self, channel: str, event: str, **payload: Any) -> None:
        safe_payload = self._sanitize(payload)
        record = {"ts": utc_now_iso(), "event": event, **safe_payload}
        logger = self._loggers.get(channel) or self._loggers["session"]
        logger.info(json.dumps(record, ensure_ascii=False, default=str))

    def exception(self, channel: str, event: str, exc: BaseException, **payload: Any) -> None:
        self.log(
            channel,
            event,
            error_type=exc.__class__.__name__,
            error=str(exc),
            traceback=traceback.format_exc(),
            **payload,
        )

    def emergency_stop(self, command_id: str, reason: str, **payload: Any) -> None:
        self.log(
            "go2",
            "emergency_stop",
            command_id=command_id,
            reason=reason,
            emergency_stop=True,
            **payload,
        )

    def close(self) -> None:
        for logger in self._loggers.values():
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, dict):
            redacted = {}
            for key, item in value.items():
                if any(token in str(key).lower() for token in ["key", "token", "secret"]):
                    redacted[key] = "***"
                elif str(key) == "raw_result":
                    redacted[key] = "<omitted>"
                else:
                    redacted[key] = self._sanitize(item)
            return redacted
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        return value
