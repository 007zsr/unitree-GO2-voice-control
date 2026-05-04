from __future__ import annotations

import re

from src.models import SemanticResult
from src.nlu.keyword_candidate import detect_source_language


class FuzzyCommandResolver:
    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def resolve(self, text: str) -> SemanticResult | None:
        if not bool(self.config.get("enabled", True)):
            return None
        cleaned = " ".join(str(text or "").strip().split())
        if not cleaned:
            return None
        lowered = cleaned.lower()
        if self._user_on_left(cleaned, lowered):
            return self._result(
                cleaned,
                "turn_left",
                0.72,
                False,
                "User said they are on the robot's left side; safe inference is turn_left only.",
                "owner_left_relative_direction",
            )
        if self._user_on_right(cleaned, lowered):
            return self._result(
                cleaned,
                "turn_right",
                0.72,
                False,
                "User said they are on the robot's right side; safe inference is turn_right only.",
                "owner_right_relative_direction",
            )
        if self._asks_to_come_here(cleaned, lowered):
            return SemanticResult(
                is_command=True,
                intent="unknown_relative_move",
                duration_sec=None,
                speed_level="slow",
                source_language=detect_source_language(cleaned),
                confidence=0.4,
                need_clarification=True,
                dangerous=False,
                reason=(
                    "User asked the robot to come here, but no visual, audio, or map-based "
                    "relative direction is available."
                ),
                raw_result={
                    "provider": "fuzzy_rule",
                    "text": cleaned,
                    "inferred": True,
                    "inference_reason": "unknown_relative_move_without_direction",
                    "allow_auto_move_to_speaker": bool(
                        self.config.get("allow_auto_move_to_speaker", False)
                    ),
                },
            )
        if self._asks_to_rest(cleaned, lowered):
            return self._result(
                cleaned,
                "sit_down",
                0.65,
                False,
                "User used a rest/sleep expression; safe candidate is sit_down.",
                "rest_or_sleep_expression",
            )
        return None

    def _result(
        self,
        text: str,
        intent: str,
        confidence: float,
        need_clarification: bool,
        reason: str,
        inference_reason: str,
    ) -> SemanticResult:
        return SemanticResult(
            is_command=True,
            intent=intent,
            duration_sec=None,
            speed_level="slow",
            source_language=detect_source_language(text),
            confidence=confidence,
            need_clarification=need_clarification,
            dangerous=False,
            reason=reason,
            raw_result={
                "provider": "fuzzy_rule",
                "text": text,
                "inferred": True,
                "inference_reason": inference_reason,
            },
        )

    def _asks_to_come_here(self, original: str, lowered: str) -> bool:
        return bool(
            re.search(r"\bcome here\b", lowered)
            or re.search(r"\bcome\s+to\s+me\b", lowered)
            or re.search(r"\bcome\s+closer\b", lowered)
            or re.search(r"\bmove\s+closer\s+to\s+me\b", lowered)
            or "过来" in original
            or "来这里" in original
            or "来我这里" in original
            or "到我这边来" in original
            or "到主人这边来" in original
            or "靠近我" in original
        )

    def _user_on_left(self, original: str, lowered: str) -> bool:
        return bool(
            re.search(r"\b(i am|i'm|im)\s+(on|to)\s+your\s+left\b", lowered)
            or re.search(r"\b(i am|i'm|im)\s+standing\s+on\s+your\s+left\b", lowered)
            or re.search(r"\bon\s+your\s+left\b", lowered)
            or re.search(r"\bowner\s+is\s+on\s+the\s+left\b", lowered)
            or re.search(r"\byour\s+owner\s+is\s+on\s+the\s+left\b", lowered)
            or re.search(r"\bface\s+me\b.*\bon\s+your\s+left\b", lowered)
            or re.search(r"\bturn\s+toward\s+me\s+from\s+your\s+left\s+side\b", lowered)
            or re.search(r"\blook\s+to\s+your\s+left\b.*\bi\s+am\s+here\b", lowered)
            or "我在你左边" in original
            or "我在你左手边" in original
            or "我在左边" in original
            or "主人在你左边" in original
            or "主人在左边" in original
            or ("往我这边看" in original and "左边" in original)
        )

    def _user_on_right(self, original: str, lowered: str) -> bool:
        return bool(
            re.search(r"\b(i am|i'm|im)\s+(on|to)\s+your\s+right\b", lowered)
            or re.search(r"\b(i am|i'm|im)\s+standing\s+on\s+your\s+right\b", lowered)
            or re.search(r"\bon\s+your\s+right\b", lowered)
            or re.search(r"\bowner\s+is\s+on\s+the\s+right\b", lowered)
            or re.search(r"\byour\s+owner\s+is\s+on\s+the\s+right\b", lowered)
            or re.search(r"\bface\s+me\b.*\bon\s+your\s+right\b", lowered)
            or re.search(r"\bturn\s+toward\s+me\s+from\s+your\s+right\s+side\b", lowered)
            or re.search(r"\blook\s+to\s+your\s+right\b.*\bi\s+am\s+here\b", lowered)
            or "我在你右边" in original
            or "我在你右手边" in original
            or "我在右边" in original
            or "主人在你右边" in original
            or "主人在右边" in original
            or ("往我这边看" in original and "右边" in original)
        )

    def _asks_to_rest(self, original: str, lowered: str) -> bool:
        return bool(
            re.search(r"\b(sleep|take a rest|rest)\b", lowered)
            or "休息一下" in original
            or "睡一会" in original
        )
