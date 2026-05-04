from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class AsrTextNormalization:
    original_text: str
    normalized_text: str
    ambiguity_flags: list[str] = field(default_factory=list)
    reject_reason: str = ""
    needs_confirmation: bool = False
    inferred_intent: str = ""
    confidence: float | None = None

    @property
    def changed(self) -> bool:
        return self.normalized_text != self.original_text

    def to_dict(self) -> dict[str, object]:
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "ambiguity_flags": self.ambiguity_flags,
            "reject_reason": self.reject_reason,
            "needs_confirmation": self.needs_confirmation,
            "inferred_intent": self.inferred_intent,
            "confidence": self.confidence,
            "changed": self.changed,
        }


class AsrTextNormalizer:
    def normalize(self, text: str, command_detection_mode: str = "strict") -> AsrTextNormalization:
        original = " ".join(str(text or "").strip().split())
        lowered = original.lower()
        mode = str(command_detection_mode or "strict").lower()

        if re.search(r"\bturn\s+off\b", lowered) and re.search(r"\bturn\s+(left|right)\b", lowered):
            return AsrTextNormalization(
                original_text=original,
                normalized_text=original,
                ambiguity_flags=["ambiguous_turn_off_phrase"],
                reject_reason="ambiguous_turn_off_phrase",
                needs_confirmation=True,
            )

        if re.search(r"\bturn\s+of\s+the\s+turn\s+(left|right)\b", lowered):
            return AsrTextNormalization(
                original_text=original,
                normalized_text=original,
                ambiguity_flags=["ambiguous_turn_of_phrase"],
                reject_reason="ambiguous_turn_of_phrase",
                needs_confirmation=False,
            )

        near_miss_patterns = [
            (r"\bsit\s+(town|dawn)\b", "ambiguous_sit_near_miss"),
            (r"\bstand\s+(town|app)\b", "ambiguous_stand_near_miss"),
            (r"\bstop\s+it\s+maybe\b", "uncertain_stop_phrase"),
            (r"\blife\s+right\b", "ambiguous_direction_phrase"),
            (r"\bturn\s+(write|ride|light)\b", "ambiguous_turn_near_miss"),
            (r"\bmove\s+(for\s+word|foreword|bark)\b", "ambiguous_move_near_miss"),
        ]
        for pattern, reason in near_miss_patterns:
            if re.search(pattern, lowered):
                return AsrTextNormalization(
                    original_text=original,
                    normalized_text=original,
                    ambiguity_flags=[reason],
                    reject_reason=reason,
                    needs_confirmation=False,
                )

        if re.search(r"\bturn\s+(life|live)\b", lowered):
            if mode == "relaxed":
                return AsrTextNormalization(
                    original_text=original,
                    normalized_text=re.sub(r"\bturn\s+(life|live)\b", "turn left", original, flags=re.IGNORECASE),
                    ambiguity_flags=["ambiguous_asr_turn_left"],
                    needs_confirmation=False,
                    inferred_intent="turn_left",
                    confidence=0.55,
                )
            return AsrTextNormalization(
                original_text=original,
                normalized_text=original,
                ambiguity_flags=["ambiguous_asr_turn_left"],
                reject_reason="ambiguous_asr_turn_left",
                needs_confirmation=True,
                inferred_intent="turn_left",
                confidence=0.55,
            )

        return AsrTextNormalization(original_text=original, normalized_text=original)
