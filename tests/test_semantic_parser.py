from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.nlu.semantic_parser import SemanticParseError, SemanticParser


class SemanticParserTest(unittest.TestCase):
    def test_valid_json(self) -> None:
        result = SemanticParser().parse(
            '{"is_command":true,"intent":"turn_left","duration_sec":0.7,"speed_level":"slow",'
            '"confidence":0.91,"need_clarification":false,'
            '"dangerous":false,"reason":"left"}'
        )
        self.assertTrue(result.is_command)
        self.assertEqual(result.intent, "turn_left")
        self.assertEqual(result.duration_sec, 0.7)

    def test_rejects_non_json(self) -> None:
        with self.assertRaises(SemanticParseError):
            SemanticParser().parse("turn left")

    def test_rejects_sdk_tokens(self) -> None:
        with self.assertRaises(SemanticParseError):
            SemanticParser().parse(
                '{"is_command":true,"intent":"move_forward","duration_sec":1.0,"speed_level":"slow",'
                '"confidence":0.9,"need_clarification":false,'
                '"dangerous":false,"reason":"call SportClient.Move(0.3,0,0)"}'
            )


if __name__ == "__main__":
    unittest.main()
