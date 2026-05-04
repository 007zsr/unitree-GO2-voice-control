from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from src.commands.go2_action_catalog import ActionAliasMatch, Go2ActionCatalog
from src.models import SemanticResult
from src.nlu.keyword_candidate import detect_source_language, find_command_candidate
from src.nlu.non_command_filter import NonCommandFilter
from src.nlu.prompt_builder import PromptBuilder
from src.nlu.semantic_parser import SemanticParseError, SemanticParser


class QwenEngine:
    STOP_PHRASES = [
        "停",
        "停下",
        "停止",
        "别动",
        "立刻停",
        "不要动",
        "原地待命",
        "原地别动",
        "保持不动",
        "停在原地",
        "别移动",
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
    ]
    DANGEROUS_KEYWORDS = [
        "攻击",
        "撞",
        "撞击",
        "冲过去",
        "扑",
        "扑击",
        "跳",
        "跳跃",
        "翻跟头",
        "后空翻",
        "快跑",
        "高速",
        "attack",
        "crash",
        "hit",
        "jump",
        "flip",
        "backflip",
        "run fast",
        "sprint",
        "charge",
    ]
    FAST_KEYWORDS = ["快", "快点", "高速", "快跑", "fast", "quickly", "run", "sprint"]
    NUMBER_WORDS = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "half": 0.5,
    }
    CHINESE_NUMBERS = {
        "半": 0.5,
        "一": 1,
        "两": 2,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    EN_EXAMPLE_MARKERS = ["i said", "example", "phrase", "word", "appears here", "means"]
    ZH_EXAMPLE_MARKERS = ["这个词", "这句话", "例子", "举例", "刚才说", "意思是"]

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.prompt_builder = PromptBuilder()
        self.parser = SemanticParser()
        self.non_command_filter = NonCommandFilter()
        self.action_catalog = Go2ActionCatalog(
            config.get("go2_action_catalog") or config.get("action_catalog") or {}
        )

    def parse_command(self, text: str) -> SemanticResult:
        cleaned = " ".join(text.strip().split())
        if not cleaned:
            return SemanticResult(
                is_command=False,
                intent="none",
                source_language="unknown",
                confidence=0.0,
                need_clarification=True,
                reason="Input text is empty.",
            )
        non_command = self.non_command_filter.classify(cleaned)
        if self._command_detection_mode() == "strict" and non_command.is_non_command:
            return SemanticResult(
                is_command=False,
                intent="none",
                source_language=detect_source_language(cleaned),
                confidence=0.95,
                need_clarification=False,
                dangerous=False,
                reason=non_command.reason,
                raw_result={
                    "provider": "non_command_filter",
                    "text": cleaned,
                    "non_command_reason": non_command.reason,
                },
            )
        if self._is_stop(cleaned):
            return SemanticResult(
                is_command=True,
                intent="stop",
                duration_sec=0.0,
                speed_level="slow",
                source_language=detect_source_language(cleaned),
                confidence=1.0,
                dangerous=False,
                need_clarification=False,
                reason="Stop command has highest priority.",
                raw_result={"provider": "rule_based", "text": cleaned, "is_command": True},
            )

        dangerous_semantic = self._parse_dangerous_action(cleaned)
        if dangerous_semantic is not None:
            return dangerous_semantic

        catalog_semantic = self._parse_with_action_catalog(cleaned)
        if catalog_semantic is not None:
            return catalog_semantic

        provider = str(self.config.get("provider") or self.config.get("mode") or "rule_based")
        if provider in {"rule_based", "mock", "local_rule"}:
            return self._rule_based_parse(cleaned)

        try:
            raw = self._call_remote_qwen(cleaned)
            return self.parser.parse(raw)
        except (SemanticParseError, RuntimeError, urllib.error.URLError, TimeoutError) as exc:
            if bool(self.config.get("allow_rule_fallback", True)):
                result = self._rule_based_parse(cleaned)
                result.reason = f"{result.reason}; Qwen fallback after error: {exc}"
                return result
            return SemanticResult(
                is_command=False,
                intent="none",
                source_language=detect_source_language(cleaned),
                confidence=0.0,
                need_clarification=True,
                dangerous=False,
                reason=f"Qwen parse failed: {exc}",
            )

    def _call_remote_qwen(self, text: str) -> str:
        endpoint = str(self.config.get("endpoint") or os.getenv("QWEN_ENDPOINT") or "")
        if not endpoint:
            raise RuntimeError("Qwen endpoint is not configured")
        api_key_env = str(self.config.get("api_key_env") or "QWEN_API_KEY")
        api_key = os.getenv(api_key_env, "")
        payload = {
            "model": os.getenv("QWEN_MODEL") or self.config.get("model", "qwen-plus"),
            "messages": self.prompt_builder.build(text),
            "temperature": float(self.config.get("temperature", 0)),
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        timeout = float(self.config.get("timeout_sec", 8))
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        if isinstance(data, dict):
            if "choices" in data:
                return str(data["choices"][0]["message"]["content"])
            if "content" in data:
                return str(data["content"])
            if "output" in data:
                output = data["output"]
                if isinstance(output, dict) and "text" in output:
                    return str(output["text"])
        raise RuntimeError("Qwen response format is unsupported")

    def _rule_based_parse(self, text: str) -> SemanticResult:
        lowered = text.lower()
        source_language = detect_source_language(text)
        candidate = find_command_candidate(text)
        dangerous = self._is_dangerous(lowered, text)
        duration = self._parse_duration_sec(text)
        speed_level = "fast" if self._is_fast_request(lowered, text) else "slow"

        if (
            candidate.is_candidate
            and self._command_detection_mode() == "strict"
            and self._is_single_direction_fragment(text)
        ):
            return self._semantic(
                text,
                is_command=False,
                intent="none",
                source_language=source_language,
                duration=duration,
                speed_level=speed_level,
                dangerous=False,
                reason="single_direction_word_rejected_in_strict_mode",
                confidence=0.0,
                candidate=candidate,
            )

        if (
            candidate.is_candidate
            and self._command_detection_mode() == "strict"
            and not dangerous
            and not self._strict_allows(text, lowered)
        ):
            return self._semantic(
                text,
                is_command=False,
                intent="none",
                source_language=source_language,
                duration=duration,
                speed_level=speed_level,
                dangerous=False,
                reason="Strict mode ignored a command keyword inside a non-command sentence.",
                confidence=0.75,
                candidate=candidate,
            )

        intent = "none"
        reason = "No robot command keyword found."
        is_command = False
        need_clarification = False
        confidence = 0.8

        if self._contains_any(text, lowered, ["站起来", "起立"], ["stand up", "get up"]):
            intent, reason, is_command, confidence = "stand_up", "Rule parser matched stand-up command.", True, 0.9
        elif self._contains_any(text, lowered, ["坐下", "趴下"], ["sit down", "lie down"]):
            intent, reason, is_command, confidence = "sit_down", "Rule parser matched sit-down command.", True, 0.9
        elif self._contains_any(
            text,
            lowered,
            ["向前", "往前", "前进", "朝前"],
            ["move forward", "go forward", "walk forward", "forward"],
        ):
            intent, reason, is_command, confidence = "move_forward", "Rule parser matched forward movement.", True, 0.9
        elif self._contains_any(
            text,
            lowered,
            ["后退", "往后", "退后", "向后"],
            ["move back", "go back", "move backward", "go backward", "backward"],
        ):
            intent, reason, is_command, confidence = "move_backward", "Rule parser matched backward movement.", True, 0.9
        elif self._contains_any(text, lowered, ["左转", "向左转", "往左"], ["turn left", "left"]):
            intent, reason, is_command, confidence = "turn_left", "Rule parser matched left turn.", True, 0.9
        elif self._contains_any(text, lowered, ["右转", "向右转", "往右"], ["turn right", "right"]):
            intent, reason, is_command, confidence = "turn_right", "Rule parser matched right turn.", True, 0.9
        elif self._contains_any(
            text,
            lowered,
            ["报告状态", "状态", "电量"],
            ["report status", "status", "battery"],
        ):
            intent, reason, is_command, confidence = "status_report", "Rule parser matched status report.", True, 0.9
        elif dangerous:
            intent, reason, is_command, confidence = "unknown", "Dangerous robot request detected.", True, 0.2
        elif candidate.is_candidate:
            intent = "unknown"
            reason = "Possible robot command keyword found, but action is unclear."
            is_command = True
            need_clarification = True
            confidence = 0.2

        result = self._semantic(
            text,
            is_command=is_command,
            intent=intent,
            source_language=source_language,
            duration=duration,
            speed_level=speed_level,
            dangerous=dangerous,
            reason=reason,
            confidence=confidence,
            candidate=candidate,
        )
        result.need_clarification = need_clarification
        return result

    def _parse_with_action_catalog(self, text: str) -> SemanticResult | None:
        match = self.action_catalog.match_text(text)
        if match is None:
            return None
        lowered = text.lower()
        if (
            self._command_detection_mode() == "strict"
            and match.action.risk_level not in {"dangerous", "disabled"}
            and not self._is_dangerous(lowered, text)
            and self._is_single_direction_fragment(text)
        ):
            return SemanticResult(
                is_command=False,
                intent="none",
                source_language=detect_source_language(text),
                confidence=0.0,
                need_clarification=False,
                dangerous=False,
                reason="single_direction_word_rejected_in_strict_mode",
                raw_result={
                    "provider": "catalog_alias",
                    "matched_alias": match.alias,
                    "risk_level": match.action.risk_level,
                },
            )
        if (
            self._command_detection_mode() == "strict"
            and match.action.risk_level not in {"dangerous", "disabled"}
            and not self._is_dangerous(lowered, text)
            and not self._strict_allows(text, lowered)
        ):
            return SemanticResult(
                is_command=False,
                intent="none",
                source_language=detect_source_language(text),
                confidence=0.75,
                need_clarification=False,
                dangerous=False,
                reason="Strict mode ignored a command keyword inside a non-command sentence.",
                raw_result={
                    "provider": "catalog_alias",
                    "matched_alias": match.alias,
                    "risk_level": match.action.risk_level,
                },
            )
        return self._semantic_from_action_match(text, match)

    def _parse_dangerous_action(self, text: str) -> SemanticResult | None:
        lowered = text.lower()
        intent = ""
        alias = ""
        if re.search(r"\b(front\s+flip|flip\s+forward|forward\s+flip)\b", lowered) or "前空翻" in text:
            intent, alias = "front_flip", "front flip"
        elif re.search(r"\b(back\s+flip|backflip|flip\s+backward)\b", lowered) or "后空翻" in text:
            intent, alias = "back_flip", "back flip"
        elif re.search(r"\b(flip\s+(to\s+the\s+)?left|left\s+flip)\b", lowered) or "左翻" in text:
            intent, alias = "left_flip", "left flip"
        elif re.search(r"\b(free\s+jump)\b", lowered) or "自由跳" in text:
            intent, alias = "free_jump", "free jump"
        elif re.search(r"\b(jump\s+forward|front\s+jump)\b", lowered) or "向前跳" in text or "跳一下" in text:
            intent, alias = "front_jump", "front jump"
        elif re.search(r"\b(pounce\s+forward|front\s+pounce|pounce)\b", lowered) or "向前扑" in text or "扑" in text:
            intent, alias = "front_pounce", "front pounce"
        elif re.search(r"\b(hand\s*stand|handstand)\b", lowered) or "倒立" in text:
            intent, alias = "hand_stand", "hand stand"
        elif re.search(r"\b(run\s+fast|sprint|trot\s+run)\b", lowered) or "快跑" in text or "高速跑" in text:
            intent, alias = "trot_run", "run fast"
        elif re.search(r"\bscrape\b", lowered) or "刮擦" in text:
            intent, alias = "scrape", "scrape"
        elif re.search(r"\b(walk\s+upright|upright\s+walk)\b", lowered) or "直立行走" in text:
            intent, alias = "walk_upright", "walk upright"
        if not intent:
            return None
        action = self.action_catalog.get(intent)
        if action is None:
            return SemanticResult(
                is_command=True,
                intent="unknown",
                source_language=detect_source_language(text),
                confidence=0.2,
                need_clarification=True,
                dangerous=True,
                risk_level="dangerous",
                reason="Dangerous robot request detected.",
                raw_result={"provider": "dangerous_action_detector", "text": text},
            )
        return self._semantic_from_action_match(
            text,
            ActionAliasMatch(
                action=action,
                alias=alias,
                language=detect_source_language(text),
                confidence=0.95,
            ),
        )

    def _semantic_from_action_match(self, text: str, match: ActionAliasMatch) -> SemanticResult:
        action = match.action
        lowered = text.lower()
        dangerous = action.risk_level == "dangerous" or self._is_dangerous(lowered, text)
        speed_level = "fast" if self._is_fast_request(lowered, text) else "slow"
        rejected_by_nlu = action.risk_level == "disabled"
        executable = (
            action.voice_enabled
            and not rejected_by_nlu
            and action.risk_level != "dangerous"
        )
        needs_confirmation = (
            action.requires_manual_confirm
            or rejected_by_nlu
            or action.risk_level == "dangerous"
            or not action.voice_enabled
        )
        if action.risk_level == "dangerous":
            reason = "Dangerous catalog action recognized; voice execution is disabled by default."
        elif action.risk_level == "disabled":
            reason = "Catalog action is disabled for this project."
        elif action.risk_level == "caution":
            reason = "Caution catalog action recognized; Safety decides real-robot availability."
        else:
            reason = "Catalog alias matched a supported Go2 action."
        return SemanticResult(
            is_command=True,
            intent=action.intent,
            duration_sec=self._parse_duration_sec(text),
            speed_level=speed_level,
            source_language=match.language or detect_source_language(text),
            confidence=match.confidence,
            need_clarification=needs_confirmation,
            dangerous=dangerous,
            risk_level=action.risk_level,
            executable=executable,
            rejected_by_nlu=rejected_by_nlu,
            reason=reason,
            raw_output="",
            raw_result={
                "provider": "catalog_alias",
                "text": text,
                "is_command": True,
                "intent": action.intent,
                "official_name": action.official_name,
                "sdk_method": action.sdk_method,
                "risk_level": action.risk_level,
                "voice_enabled": action.voice_enabled,
                "mock_enabled": action.mock_enabled,
                "real_robot_enabled": action.real_robot_enabled,
                "requires_manual_confirm": action.requires_manual_confirm,
                "matched_alias": match.alias,
                "matched_language": match.language,
                "executable": executable,
                "rejected_by_nlu": rejected_by_nlu,
            },
        )

    def _semantic(
        self,
        text: str,
        is_command: bool,
        intent: str,
        source_language: str,
        duration: float | None,
        speed_level: str,
        dangerous: bool,
        reason: str,
        confidence: float,
        candidate,
    ) -> SemanticResult:
        return SemanticResult(
            is_command=is_command,
            intent=intent,
            duration_sec=duration,
            speed_level=speed_level,
            source_language=source_language,
            confidence=confidence,
            need_clarification=False,
            dangerous=dangerous,
            risk_level="dangerous" if dangerous else "safe",
            executable=True,
            reason=reason,
            raw_output="",
            raw_result={
                "provider": "rule_based",
                "text": text,
                "is_command": is_command,
                "command_detection_mode": self._command_detection_mode(),
                "recognition_preference": self._recognition_preference(),
                "matched_in_relaxed_mode": (
                    self._command_detection_mode() == "relaxed"
                    and self._is_single_direction_fragment(text)
                    and is_command
                ),
                "keyword_candidate": {
                    "is_candidate": candidate.is_candidate,
                    "matched_keywords": candidate.matched_keywords,
                    "source_language": candidate.source_language,
                },
            },
        )

    def _command_detection_mode(self) -> str:
        command_detection = self.config.get("command_detection", {})
        return str(command_detection.get("mode", "strict")).lower()

    def _recognition_preference(self) -> str:
        recognition = self.config.get("recognition", {})
        return str(recognition.get("preference", "auto")).lower()

    def _strict_allows(self, original: str, lowered: str) -> bool:
        if self._contains_example_marker(original, lowered):
            return False
        prefixes = self.config.get("command_detection", {}).get("command_prefixes", {})
        zh_prefixes = list(prefixes.get("zh", ["机器狗", "小狗", "狗狗", "请"]))
        en_prefixes = list(prefixes.get("en", ["go2", "robot", "dog", "please"]))
        if any(prefix and prefix in original for prefix in zh_prefixes):
            return True
        if any(re.search(rf"\b{re.escape(prefix.lower())}\b", lowered) for prefix in en_prefixes if prefix):
            return True
        words = re.findall(r"[a-zA-Z]+", original)
        if len(words) == 1 and words[0].lower() in {"right", "left", "forward", "back", "backward"}:
            return False
        has_zh = bool(re.search(r"[\u4e00-\u9fff]", original))
        if words and words[0].lower() in {
            "move",
            "go",
            "walk",
            "turn",
            "stand",
            "sit",
            "stop",
            "halt",
            "freeze",
            "please",
        }:
            return True
        if words and len(words) <= 4:
            return True
        compact_zh = re.sub(r"[^\u4e00-\u9fff]", "", original)
        if has_zh and len(compact_zh) <= 8:
            return True
        if lowered.endswith("please") or lowered.startswith("please "):
            return True
        return False

    def _is_single_direction_fragment(self, original: str) -> bool:
        words = re.findall(r"[a-zA-Z]+", original)
        if len(words) == 1 and words[0].lower() in {"right", "left", "forward", "back", "backward"}:
            return True
        compact_zh = re.sub(r"[^\u4e00-\u9fff]", "", original)
        return compact_zh in {"左", "右", "前", "后"}

    def _contains_example_marker(self, original: str, lowered: str) -> bool:
        if any(marker in lowered for marker in self.EN_EXAMPLE_MARKERS):
            return True
        return any(marker in original for marker in self.ZH_EXAMPLE_MARKERS)

    def _is_stop(self, text: str) -> bool:
        lowered = text.lower()
        compact_zh = re.sub(r"[^\u4e00-\u9fff]", "", text)
        if compact_zh in {
            "停",
            "停下",
            "停止",
            "别动",
            "立刻停",
            "不要动",
            "原地待命",
            "原地别动",
            "保持不动",
            "停在原地",
            "别移动",
            "停止移动",
        }:
            return True
        return any(
            phrase == text
            or phrase.lower() == lowered
            or (
                phrase in {"stop", "halt", "freeze"}
                and re.fullmatch(rf"\s*(?:please\s+)?{phrase}(?:\s+now)?\s*[.!?]*\s*", lowered)
            )
            or (
                phrase
                in {
                    "do not move",
                    "don't move",
                    "hold still",
                    "stay still",
                    "stay there",
                    "stand still",
                    "stop moving",
                }
                and re.fullmatch(rf"\s*(?:please\s+)?{re.escape(phrase)}\s*[.!?]*\s*", lowered)
            )
            for phrase in self.STOP_PHRASES
        )

    def _is_dangerous(self, lowered: str, original: str) -> bool:
        if "跳舞" in original or "舞蹈" in original:
            stripped = original.replace("跳舞", "").replace("舞蹈", "")
            lowered_stripped = stripped.lower()
            return any(
                keyword not in {"跳", "跳跃"}
                and (keyword.lower() in lowered_stripped or keyword in stripped)
                for keyword in self.DANGEROUS_KEYWORDS
            )
        return any(keyword.lower() in lowered or keyword in original for keyword in self.DANGEROUS_KEYWORDS)

    def _is_fast_request(self, lowered: str, original: str) -> bool:
        return any(keyword.lower() in lowered or keyword in original for keyword in self.FAST_KEYWORDS)

    def _contains_any(
        self,
        original: str,
        lowered: str,
        zh_phrases: list[str],
        en_phrases: list[str],
    ) -> bool:
        if any(phrase in original for phrase in zh_phrases):
            return True
        return any(re.search(rf"\b{re.escape(phrase)}\b", lowered) for phrase in en_phrases)

    def _parse_duration_sec(self, text: str) -> float | None:
        lowered = text.lower()
        number_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:秒|s|sec|secs|second|seconds)(?:\b|$)",
            lowered,
        )
        if number_match:
            return float(number_match.group(1))
        for token, value in self.CHINESE_NUMBERS.items():
            if re.search(rf"{re.escape(token)}\s*秒", text):
                return float(value)
        for token, value in self.NUMBER_WORDS.items():
            if re.search(rf"\b{token}\s*(?:s|sec|secs|second|seconds)\b", lowered):
                return float(value)
        return None
