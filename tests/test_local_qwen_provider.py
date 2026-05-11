from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.nlu.local_qwen_provider import LocalQwenProvider, check_local_qwen_model
from src.nlu.llm_provider_base import LLMProviderContext
from src.models import SemanticResult


class LocalQwenProviderTest(unittest.TestCase):
    def test_missing_model_dir_is_unavailable_without_download(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "models" / "qwen"
            status = check_local_qwen_model(missing, root)
            self.assertFalse(status.available)
            self.assertEqual(status.reason, "model_dir_missing")
            self.assertFalse(missing.exists())

    def test_provider_degrades_when_model_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            provider = LocalQwenProvider({"local_llm_model_dir": "models/qwen"}, root)
            result = provider.generate(
                LLMProviderContext(
                    normalized_text="Take a seat.",
                    asr_language="en",
                    rule_nlu_result=SemanticResult(False, "none"),
                    allowed_intents=["sit_down", "unknown"],
                    action_catalog_summary=[],
                    safety_policy_summary="SafetyController decides execution.",
                    semantic_engine_mode="llm_fallback",
                )
            )
            self.assertFalse(result.available)
            self.assertEqual(result.error_type, "model_dir_missing")
            self.assertFalse((root / "models" / "qwen").exists())


if __name__ == "__main__":
    unittest.main()
