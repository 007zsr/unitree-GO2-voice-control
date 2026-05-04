from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class SequenceParseResult:
    spans: list[str]
    truncated: bool = False
    truncated_count: int = 0
    connectors_found: list[str] = field(default_factory=list)


class SequenceCommandParser:
    EN_CONNECTORS = [
        "and then",
        "after that",
        "then",
        "next",
    ]
    ZH_CONNECTORS = [
        "然后",
        "接着",
        "之后",
        "再",
    ]
    EN_COMMAND_WORDS = [
        "stand",
        "sit",
        "move",
        "go",
        "walk",
        "turn",
        "stop",
        "halt",
        "freeze",
        "status",
        "battery",
        "forward",
        "backward",
        "left",
        "right",
    ]
    ZH_COMMAND_WORDS = [
        "站",
        "起立",
        "坐",
        "趴",
        "前",
        "后",
        "左",
        "右",
        "停",
        "状态",
        "电量",
    ]

    def __init__(
        self,
        max_commands: int = 3,
        extra_en_words: list[str] | None = None,
        extra_zh_words: list[str] | None = None,
    ):
        self.max_commands = max_commands
        self.extra_en_words = extra_en_words or []
        self.extra_zh_words = extra_zh_words or []

    def split(self, text: str) -> SequenceParseResult:
        cleaned = self._clean(text)
        if not cleaned:
            return SequenceParseResult([])

        if self._looks_like_relative_fuzzy(cleaned):
            return SequenceParseResult([cleaned])

        connectors = self._find_connectors(cleaned)
        parts = self._split_on_connectors(cleaned)
        if "," in cleaned:
            expanded: list[str] = []
            for part in parts:
                expanded.extend(self._split_on_commas(part) if "," in part else [part])
            parts = expanded
        has_plan_context = bool(connectors) or self._has_zh_plan_context(cleaned)
        spans = [
            self._normalize_short_direction_span(self._strip_prefix(part), has_plan_context)
            for part in parts
        ]
        spans = [span for span in spans if span and self._contains_command_word(span)]
        if not spans and self._contains_command_word(cleaned):
            spans = [cleaned]

        truncated = len(spans) > self.max_commands
        truncated_count = max(0, len(spans) - self.max_commands)
        return SequenceParseResult(
            spans=spans[: self.max_commands],
            truncated=truncated,
            truncated_count=truncated_count,
            connectors_found=connectors,
        )

    def _clean(self, text: str) -> str:
        return " ".join(str(text or "").replace("，", ",").replace("。", ".").split()).strip()

    def _split_on_connectors(self, text: str) -> list[str]:
        pattern = r"\b(?:and\s+then|after\s+that|then|next)\b|然后|接着|之后|再"
        return [part.strip(" ,.;，。") for part in re.split(pattern, text, flags=re.IGNORECASE) if part.strip(" ,.;，。")]

    def _split_on_commas(self, text: str) -> list[str]:
        return [part.strip(" ,.;，。") for part in re.split(r"[,;]", text) if part.strip(" ,.;，。")]

    def _strip_prefix(self, span: str) -> str:
        stripped = span.strip()
        lowered = stripped.lower()
        patterns = [
            r"^(hi|hey|hello)\s+(go2|robot|dog)\s*",
            r"^(go2|robot|dog)\s*",
            r"^please\s+",
            r"^first\s+",
            r"^先\s*",
            r"^(机器狗|小狗|狗狗)[，,\s]*",
            r"^请\s*",
        ]
        for pattern in patterns:
            stripped = re.sub(pattern, "", stripped, flags=re.IGNORECASE).strip(" ,.;，。")
        if lowered != stripped.lower():
            return stripped
        return span.strip(" ,.;，。")

    def _normalize_short_direction_span(self, span: str, has_plan_context: bool) -> str:
        if not has_plan_context:
            return span
        compact = re.sub(r"[^\u4e00-\u9fff]", "", span)
        mapping = {
            "向左": "向左转",
            "往左": "向左转",
            "向右": "向右转",
            "往右": "向右转",
        }
        return mapping.get(compact, span)

    def _has_zh_plan_context(self, text: str) -> bool:
        return bool(
            any(marker in text for marker in ["先", "再", "然后", "接着", "之后"])
            or re.match(r"^\s*(请|机器狗|小狗|狗狗)", text)
        )

    def _contains_command_word(self, text: str) -> bool:
        lowered = text.lower()
        if any(re.search(rf"\b{re.escape(word)}\b", lowered) for word in self.EN_COMMAND_WORDS):
            return True
        if any(self._contains_en_phrase(lowered, word) for word in self.extra_en_words):
            return True
        if any(word and word in text for word in self.extra_zh_words):
            return True
        return any(word in text for word in self.ZH_COMMAND_WORDS)

    def _contains_en_phrase(self, lowered: str, phrase: str) -> bool:
        phrase = str(phrase or "").strip().lower()
        if not phrase:
            return False
        pattern = r"\b" + r"\s+".join(re.escape(part) for part in phrase.split()) + r"\b"
        return bool(re.search(pattern, lowered))

    def _find_connectors(self, text: str) -> list[str]:
        lowered = text.lower()
        found = [connector for connector in self.EN_CONNECTORS if connector in lowered]
        found.extend(connector for connector in self.ZH_CONNECTORS if connector in text)
        return found

    def _looks_like_relative_fuzzy(self, text: str) -> bool:
        lowered = text.lower()
        has_come_here = bool(
            re.search(r"\bcome here\b", lowered)
            or re.search(r"\bcome\s+to\s+me\b", lowered)
            or re.search(r"\bcome\s+closer\b", lowered)
            or re.search(r"\bmove\s+closer\s+to\s+me\b", lowered)
            or "过来" in text
            or "来这里" in text
            or "来我这里" in text
            or "到我这边来" in text
            or "靠近我" in text
        )
        has_orientation_request = bool(
            re.search(r"\b(turn|face|look)\s+(toward\s+)?me\b", lowered)
            or "转过来" in text
            or "看过来" in text
            or "往我这边看" in text
        )
        has_relative_side = bool(
            re.search(r"\b(on|to)\s+your\s+(left|right)\b", lowered)
            or re.search(r"\bowner\s+is\s+on\s+the\s+(left|right)\b", lowered)
            or re.search(r"\bfrom\s+your\s+(left|right)\s+side\b", lowered)
            or "你左边" in text
            or "你右边" in text
            or "你左手边" in text
            or "你右手边" in text
            or "我在左边" in text
            or "我在右边" in text
            or "主人在左边" in text
            or "主人在右边" in text
        )
        return has_relative_side and (has_come_here or has_orientation_request)
