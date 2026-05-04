from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class KeywordCandidate:
    is_candidate: bool
    matched_keywords: list[str] = field(default_factory=list)
    source_language: str = "unknown"


ZH_KEYWORDS = [
    "向前",
    "前进",
    "往前",
    "后退",
    "往后",
    "左转",
    "向左",
    "右转",
    "向右",
    "停",
    "停下",
    "停止",
    "别动",
    "不要动",
    "原地待命",
    "原地别动",
    "保持不动",
    "停在原地",
    "别移动",
    "站起来",
    "起立",
    "坐下",
    "趴下",
    "状态",
    "电量",
]

EN_KEYWORDS = [
    "forward",
    "backward",
    "back",
    "left",
    "right",
    "stop",
    "halt",
    "freeze",
    "do not move",
    "don't move",
    "hold still",
    "stay still",
    "stay there",
    "stand still",
    "stop moving",
    "stand",
    "sit",
    "lie down",
    "status",
    "battery",
]


def detect_source_language(text: str) -> str:
    has_zh = bool(re.search(r"[\u4e00-\u9fff]", text))
    has_en = bool(re.search(r"[A-Za-z]", text))
    if has_zh and has_en:
        return "mixed"
    if has_zh:
        return "zh"
    if has_en:
        return "en"
    return "unknown"


def find_command_candidate(text: str) -> KeywordCandidate:
    lowered = text.lower()
    matches: list[str] = []
    for keyword in ZH_KEYWORDS:
        if keyword in text:
            matches.append(keyword)
    for keyword in EN_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            matches.append(keyword)
    return KeywordCandidate(
        is_candidate=bool(matches),
        matched_keywords=matches,
        source_language=detect_source_language(text),
    )
