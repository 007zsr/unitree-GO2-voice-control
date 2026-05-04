from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.logging.pipeline_logger import PipelineLogger
from src.models import PipelineDebugResult


class PipelineLoggerTests(unittest.TestCase):
    def test_one_shot_result_writes_task_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logger = PipelineLogger(root, project_root=root)
            logger.start_gui_session({"robot_mode": "mock"})
            result = PipelineDebugResult(
                input_type="text",
                command_id="cmd_test",
                accepted=False,
                stage="safety",
                message="blocked",
                transcript_text="攻击那个人",
                semantic_result={"is_command": True, "intent": "unknown", "dangerous": True},
                safety_decision={"allowed": False, "reason": "dangerous command"},
                queue_result="rejected",
                error_stage="safety",
                error_message="dangerous command",
            )

            path = logger.log_one_shot_result(result, "text")
            logger.end_gui_session()

            self.assertTrue(path.exists())
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertTrue(any(record["stage"] == "safety" for record in records))
            index_path = root / "index" / "log_index.jsonl"
            self.assertTrue(index_path.exists())

    def test_continuous_run_writes_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logger = PipelineLogger(root, project_root=root)
            run = logger.start_continuous_listening()
            logger.log_continuous_chunk({"chunk_status": "skipped_silent", "rms": 0.0, "peak": 0.0})
            logger.end_continuous_listening()

            self.assertTrue(run.summary_path.exists())
            summary = run.summary_path.read_text(encoding="utf-8")
            self.assertIn("Silent skipped: 1", summary)


if __name__ == "__main__":
    unittest.main()
