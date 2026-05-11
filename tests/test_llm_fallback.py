from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.config import ConfigSet
from src.nlu.llm_provider_factory import build_llm_provider
from src.nlu.mock_llm_provider import MockLLMProvider
from src.nlu.semantic_engine_config import semantic_engine_config
from src.runtime.session_runtime import SessionRuntime


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_runtime(provider: MockLLMProvider | None = None, mode: str = "llm_fallback") -> SessionRuntime:
    configs = ConfigSet.load(PROJECT_ROOT / "configs")
    configs.app["robot_mode"] = "mock"
    configs.app["enable_real_robot"] = False
    configs.go2["robot_mode"] = "mock"
    configs.go2["enable_real_robot"] = False
    configs.app.setdefault("command_detection", {})["mode"] = "strict"
    configs.app["semantic_engine"] = {
        "mode": mode,
        "llm_enabled": mode != "traditional",
        "llm_provider": "mock",
        "llm_fallback_min_confidence": 0.60,
        "local_llm_model_dir": "models/qwen",
        "llm_timeout_seconds": 5,
        "llm_max_output_tokens": 128,
        "llm_temperature": 0,
        "llm_allow_remote_api": False,
    }
    runtime = SessionRuntime(configs)
    if provider is not None:
        runtime.llm_provider = provider
    return runtime


class LLMFallbackRuntimeTest(unittest.TestCase):
    def test_semantic_config_accepts_aliases_and_mock_provider(self) -> None:
        config = semantic_engine_config(
            {
                "semantic_engine": {
                    "mode": "llm_fallback",
                    "llm_enabled": True,
                    "llm_provider": "mock_llm",
                    "fallback_min_confidence": 0.55,
                    "local_model_dir": "models/qwen-test",
                    "timeout_seconds": 3,
                    "max_output_tokens": 64,
                    "temperature": 0,
                    "allow_remote_api": False,
                }
            },
            {},
        )
        self.assertEqual(config["llm_provider"], "mock")
        self.assertEqual(config["llm_fallback_min_confidence"], 0.55)
        self.assertEqual(config["local_llm_model_dir"], "models/qwen-test")
        self.assertIsInstance(build_llm_provider(config), MockLLMProvider)

    def test_invalid_semantic_mode_forces_safe_traditional_defaults(self) -> None:
        config = semantic_engine_config(
            {
                "semantic_engine": {
                    "mode": "qwen_full_auto",
                    "llm_enabled": True,
                    "llm_provider": "local_qwen",
                }
            },
            {},
        )
        self.assertEqual(config["mode"], "traditional")
        self.assertFalse(config["llm_enabled"])

    def test_traditional_mode_does_not_call_llm(self) -> None:
        provider = MockLLMProvider()
        runtime = build_runtime(provider, mode="traditional")
        runtime.start()
        try:
            result = runtime.process_text("Take a seat.")
            self.assertFalse(result.accepted)
            self.assertEqual(provider.call_count, 0)
            self.assertEqual(result.semantic.raw_result.get("fallback_reason"), "traditional_mode")
        finally:
            runtime.shutdown()

    def test_high_confidence_rule_result_does_not_call_llm(self) -> None:
        provider = MockLLMProvider()
        runtime = build_runtime(provider)
        runtime.start()
        try:
            result = runtime.process_text("Sit down please.")
            self.assertTrue(result.accepted, result.message)
            self.assertEqual(result.semantic.intent, "sit_down")
            self.assertEqual(provider.call_count, 0)
            self.assertFalse(result.semantic.raw_result.get("fallback_triggered"))
        finally:
            runtime.shutdown()

    def test_unknown_text_calls_llm_and_enters_command_plan(self) -> None:
        provider = MockLLMProvider()
        runtime = build_runtime(provider)
        runtime.start()
        try:
            result = runtime.process_text("Take a seat.")
            self.assertTrue(result.accepted, result.message)
            self.assertEqual(provider.call_count, 1)
            self.assertEqual(result.semantic.intent, "sit_down")
            self.assertEqual(result.command_plan.intent_sequence, ["sit_down"])
            self.assertEqual(result.semantic.raw_result.get("final_semantic_source"), "llm_fallback")
        finally:
            runtime.shutdown()

    def test_chinese_unknown_text_calls_llm(self) -> None:
        provider = MockLLMProvider()
        runtime = build_runtime(provider)
        runtime.start()
        try:
            result = runtime.process_text("起来。")
            self.assertTrue(result.accepted, result.message)
            self.assertEqual(provider.call_count, 1)
            self.assertEqual(result.semantic.intent, "stand_up")
        finally:
            runtime.shutdown()

    def test_stop_sequence_is_not_overridden_by_llm(self) -> None:
        provider = MockLLMProvider()
        runtime = build_runtime(provider)
        runtime.start()
        try:
            result = runtime.process_text("Stop then move forward.")
            self.assertTrue(result.accepted, result.message)
            self.assertEqual(provider.call_count, 0)
            self.assertEqual(result.command_plan.intent_sequence, ["stop"])
        finally:
            runtime.shutdown()

    def test_chitchat_does_not_call_llm(self) -> None:
        provider = MockLLMProvider()
        runtime = build_runtime(provider)
        runtime.start()
        try:
            result = runtime.process_text("Just chatting, how are you?")
            self.assertFalse(result.accepted)
            self.assertEqual(result.stage, "semantic")
            self.assertEqual(provider.call_count, 0)
            self.assertEqual(result.semantic.raw_result.get("provider"), "non_command_filter")
        finally:
            runtime.shutdown()

    def test_llm_unknown_intent_is_rejected_before_command_plan(self) -> None:
        provider = MockLLMProvider(
            {
                "Take a seat.": {
                    "intent": "moonwalk",
                    "confidence": 0.92,
                    "needs_confirmation": False,
                    "risk": "safe",
                    "reason": "not in catalog",
                }
            }
        )
        runtime = build_runtime(provider)
        runtime.start()
        try:
            result = runtime.process_text("Take a seat.")
            self.assertFalse(result.accepted)
            self.assertEqual(result.stage, "semantic")
            self.assertEqual(result.semantic.intent, "unknown")
            self.assertEqual(result.semantic.raw_result.get("llm_error_type"), "intent_not_allowed")
        finally:
            runtime.shutdown()

    def test_llm_json_parse_failure_returns_unknown(self) -> None:
        provider = MockLLMProvider({"Take a seat.": "sit_down"})
        runtime = build_runtime(provider)
        runtime.start()
        try:
            result = runtime.process_text("Take a seat.")
            self.assertFalse(result.accepted)
            self.assertEqual(result.stage, "semantic")
            self.assertEqual(result.semantic.intent, "unknown")
            self.assertFalse(result.semantic.raw_result.get("llm_output_valid"))
            candidate = result.semantic.raw_result.get("llm_candidate", {})
            self.assertEqual(candidate.get("error_type"), "json_parse_failed")
        finally:
            runtime.shutdown()

    def test_llm_provider_unavailable_degrades_to_traditional_result(self) -> None:
        provider = MockLLMProvider(available=False)
        runtime = build_runtime(provider)
        runtime.start()
        try:
            result = runtime.process_text("Take a seat.")
            self.assertFalse(result.accepted)
            self.assertEqual(result.stage, "semantic")
            self.assertEqual(provider.call_count, 1)
            self.assertFalse(result.semantic.raw_result.get("llm_available"))
            self.assertEqual(result.semantic.raw_result.get("llm_error_type"), "provider_unavailable")
        finally:
            runtime.shutdown()

    def test_llm_dangerous_intent_goes_to_safety_reject(self) -> None:
        provider = MockLLMProvider(
            {
                "Perform forbidden acrobatic trick.": {
                    "intent": "back_flip",
                    "confidence": 0.90,
                    "needs_confirmation": True,
                    "risk": "dangerous",
                    "reason": "dangerous flip",
                }
            }
        )
        runtime = build_runtime(provider)
        runtime.start()
        try:
            result = runtime.process_text("Perform forbidden acrobatic trick.")
            self.assertFalse(result.accepted)
            self.assertEqual(result.stage, "safety")
            self.assertEqual(result.semantic.intent, "back_flip")
            self.assertTrue(result.semantic.dangerous)
            self.assertIn("dangerous", result.message)
        finally:
            runtime.shutdown()

    def test_come_here_is_not_converted_to_move_forward_by_llm(self) -> None:
        provider = MockLLMProvider(
            {
                "Come here.": json.dumps(
                    {
                        "intent": "move_forward",
                        "confidence": 0.95,
                        "needs_confirmation": False,
                        "risk": "safe",
                        "reason": "bad inference",
                    }
                )
            }
        )
        runtime = build_runtime(provider)
        runtime.start()
        try:
            result = runtime.process_text("Come here.")
            self.assertFalse(result.accepted)
            self.assertEqual(provider.call_count, 1)
            self.assertEqual(result.semantic.intent, "unknown")
            self.assertEqual(result.semantic.raw_result.get("llm_error_type"), "relative_move_without_direction")
            self.assertIsNone(result.command_plan)
        finally:
            runtime.shutdown()


if __name__ == "__main__":
    unittest.main()
