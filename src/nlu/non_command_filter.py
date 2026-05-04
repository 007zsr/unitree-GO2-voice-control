from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class NonCommandDecision:
    is_non_command: bool
    reason: str = ""


class NonCommandFilter:
    EN_PATTERNS = [
        r"\bi\s+said\b",
        r"\bthe\s+phrase\b",
        r"\bappears\s+in\s+this\s+sentence\b",
        r"\bdoes\s+not\s+mean\b",
        r"\bwe\s+are\s+talking\s+about\b",
        r"\bas\s+an\s+example\b",
        r"\bonly\s+a\s+word\s+here\b",
        r"\bdo\s+not\s+treat\b.*\bas\s+a\s+command\b",
        r"\bthis\s+document\s+mentions\b",
        r"\bjust\s+a\s+word\b",
        r"\bnot\s+actually\b",
        r"\bdo\s+not\s+actually\b",
        r"\bis\s+only\s+a\s+word\b",
    ]
    ZH_MARKERS = [
        "这个词",
        "这句话里面有",
        "只是举例",
        "不是命令",
        "只是一个测试词",
        "不要把",
        "别把",
        "不是当前命令",
        "只是一个词",
        "只是方向",
        "不要真的",
        "不是真的",
    ]
    STOP_EXCEPTIONS_EN = [
        r"^\s*(?:please\s+)?(?:do\s+not|don't)\s+move\s*[.!?。！？，,]*\s*$",
        r"^\s*(?:please\s+)?(?:hold|stay|stand)\s+still\s*[.!?。！？，,]*\s*$",
        r"^\s*(?:please\s+)?stay\s+there\s*[.!?。！？，,]*\s*$",
        r"^\s*(?:please\s+)?stop\s+moving\s*[.!?。！？，,]*\s*$",
    ]
    STOP_EXCEPTIONS_ZH = [
        "不要动",
        "别动",
        "原地待命",
        "原地别动",
        "保持不动",
        "停在原地",
        "别移动",
        "停止移动",
    ]

    def classify(self, text: str) -> NonCommandDecision:
        original = " ".join(str(text or "").strip().split())
        if not original:
            return NonCommandDecision(False)
        if self.is_explicit_stop_command(original):
            return NonCommandDecision(False)
        lowered = original.lower()
        if any(re.search(pattern, lowered) for pattern in self.EN_PATTERNS):
            return NonCommandDecision(True, "quoted_or_example_sentence")
        if any(marker in original for marker in self.ZH_MARKERS):
            return NonCommandDecision(True, "quoted_or_example_sentence")
        return NonCommandDecision(False)

    def is_explicit_stop_command(self, text: str) -> bool:
        original = " ".join(str(text or "").strip().split())
        lowered = original.lower()
        if any(re.search(pattern, lowered) for pattern in self.STOP_EXCEPTIONS_EN):
            return True
        compact_zh = re.sub(r"[^\u4e00-\u9fff]", "", original)
        return compact_zh in self.STOP_EXCEPTIONS_ZH
