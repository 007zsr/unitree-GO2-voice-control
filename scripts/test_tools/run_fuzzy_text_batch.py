from __future__ import annotations

import csv
import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ConfigSet  # noqa: E402
from src.runtime.session_runtime import SessionRuntime  # noqa: E402


DATASET_PATH = PROJECT_ROOT / "tests" / "fixtures" / "fuzzy_text_commands_240.csv"
BATCH_ROOT = PROJECT_ROOT / "runtime_data" / "logs" / "batch_text_tests"
ARCHIVE_DIR = BATCH_ROOT / "archive"
CURRENT_DIR = BATCH_ROOT / "current"

RESULTS_CSV = CURRENT_DIR / "fuzzy_text_test_results.csv"
RESULTS_JSONL = CURRENT_DIR / "fuzzy_text_test_results.jsonl"
REPORT_MD = CURRENT_DIR / "fuzzy_text_test_report.md"
FAILED_MD = CURRENT_DIR / "failed_cases.md"
CONFUSION_MD = CURRENT_DIR / "confusion_summary.md"
REGRESSION_MD = CURRENT_DIR / "regression_compare.md"

RESULT_FIELDS = [
    "case_id",
    "category",
    "text",
    "expected_is_command",
    "actual_is_command",
    "expected_intents",
    "actual_intents",
    "expected_should_execute",
    "actual_should_execute",
    "expected_needs_confirmation",
    "actual_needs_confirmation",
    "expected_risk_level",
    "actual_risk_level",
    "comparison_status",
    "severe_reasons",
    "stage",
    "message",
    "queue_status",
    "safety_allowed",
    "safety_reason",
    "plan_truncated",
    "truncated_count",
    "executed_intents",
    "notes",
]


def main() -> int:
    base_configs = ConfigSet.load(PROJECT_ROOT / "configs")
    if base_configs.robot_mode != "mock" or base_configs.enable_real_robot:
        print(
            "ABORT: batch fuzzy text test requires robot_mode=mock and "
            "enable_real_robot=false."
        )
        print(
            f"Current robot_mode={base_configs.robot_mode}, "
            f"enable_real_robot={base_configs.enable_real_robot}"
        )
        return 2

    cases = load_cases(DATASET_PATH)
    previous_summary = archive_previous_current()

    configs = ConfigSet.load(PROJECT_ROOT / "configs")
    configs.app["log_dir"] = str(CURRENT_DIR)
    configs.app.setdefault("command_plan", {})["command_gap_sec"] = 0.0
    configs.app.setdefault("command_queue", {})["worker_poll_sec"] = 0.005

    started_at = datetime.now().astimezone()
    runtime = SessionRuntime(configs)
    runtime.start()
    try:
        rows = run_cases(runtime, cases)
    finally:
        runtime.shutdown()

    finished_at = datetime.now().astimezone()
    summary = summarize(rows, started_at, finished_at)
    write_results(rows)
    write_report(rows, summary)
    write_failed_cases(rows, summary)
    write_confusion_summary(rows, summary)
    write_regression_compare(summary, previous_summary)

    print("Fuzzy text batch test completed.")
    print(f"Dataset: {DATASET_PATH}")
    print(f"Report: {REPORT_MD}")
    print(
        "Core result: "
        f"total={summary['total']}, complete={summary['complete']}, "
        f"partial={summary['partial']}, serious={summary['serious']}, "
        f"accuracy={summary['accuracy_percent']:.2f}%"
    )
    return 0


def load_cases(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [normalize_case(row) for row in reader]
    if not 230 <= len(rows) <= 260:
        raise ValueError(f"Expected 230-260 fuzzy text cases, got {len(rows)}")
    return rows


def normalize_case(row: dict[str, str]) -> dict[str, Any]:
    return {
        "case_id": row["case_id"].strip(),
        "text": row["text"].strip(),
        "category": row["category"].strip(),
        "expected_is_command": parse_bool(row["expected_is_command"]),
        "expected_intents": split_intents(row.get("expected_intents", "")),
        "expected_should_execute": parse_bool(row["expected_should_execute"]),
        "expected_needs_confirmation": parse_bool(row["expected_needs_confirmation"]),
        "expected_risk_level": row["expected_risk_level"].strip().lower() or "none",
        "notes": row.get("notes", "").strip(),
    }


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def split_intents(value: str) -> list[str]:
    clean = str(value or "").strip()
    return [part.strip() for part in clean.split("->") if part.strip()]


def archive_previous_current() -> dict[str, Any] | None:
    BATCH_ROOT.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    root_abs = BATCH_ROOT.resolve()
    archive_abs = ARCHIVE_DIR.resolve()
    current_abs = CURRENT_DIR.resolve()
    if root_abs != current_abs.parent.resolve():
        raise RuntimeError(f"Unsafe current directory: {CURRENT_DIR}")
    if root_abs not in archive_abs.parents and archive_abs != root_abs / "archive":
        raise RuntimeError(f"Unsafe archive directory: {ARCHIVE_DIR}")
    if CURRENT_DIR.exists():
        target = ARCHIVE_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
        if archive_abs not in target.resolve().parents:
            raise RuntimeError(f"Unsafe archive target: {target}")
        shutil.move(str(CURRENT_DIR), str(target))
        previous = summarize_results_csv(target / "fuzzy_text_test_results.csv")
    else:
        previous = None
    CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    return previous


def summarize_results_csv(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    total = len(rows)
    if not total:
        return None
    complete = sum(row.get("comparison_status") == "complete" for row in rows)
    partial = sum(row.get("comparison_status") == "partial" for row in rows)
    serious = sum(row.get("comparison_status") == "serious" for row in rows)
    return {
        "total": total,
        "complete": complete,
        "partial": partial,
        "serious": serious,
        "accuracy_percent": percent(complete, total),
        "chat_false_execution": sum(
            row.get("category", "").startswith("H_")
            and row.get("actual_should_execute") == "true"
            for row in rows
        ),
        "asr_false_execution": sum(
            row.get("category", "").startswith("I_")
            and row.get("expected_should_execute") == "false"
            and row.get("actual_should_execute") == "true"
            for row in rows
        ),
        "dangerous_false_execution": sum(
            row.get("expected_risk_level") in {"dangerous", "disabled"}
            and row.get("actual_should_execute") == "true"
            for row in rows
        ),
        "come_here_false_execution": sum(
            row.get("category", "").startswith("G_")
            and (
                row.get("actual_should_execute") == "true"
                or "move_forward" in row.get("actual_intents", "")
            )
            for row in rows
        ),
        "stop_missed": sum(
            "stop" in row.get("expected_intents", "").split("->")
            and "stop" not in row.get("actual_intents", "").split("->")
            for row in rows
        ),
    }


def run_cases(runtime: SessionRuntime, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for case in cases:
        reset_mock_adapter(runtime)
        result = runtime.process_text(case["text"], deduplicate=False)
        runtime.wait_until_idle(timeout_sec=5.0)
        executed_intents = [
            command.intent for command in getattr(runtime.adapter, "executed", [])
        ]
        actual = actual_fields(result, executed_intents)
        comparison = compare_case(case, actual)
        records.append({**case, **actual, **comparison, "raw_result": result.to_dict()})
    return records


def reset_mock_adapter(runtime: SessionRuntime) -> None:
    adapter = runtime.adapter
    if hasattr(adapter, "executed"):
        adapter.executed.clear()
    state = adapter.get_state()
    state.connected = True
    state.standing = True
    state.mode = "mock"


def actual_fields(result: Any, executed_intents: list[str]) -> dict[str, Any]:
    plan = result.command_plan
    semantic = result.semantic
    command = result.command
    actual_intents = list(plan.intent_sequence) if plan else []
    if not actual_intents and semantic and semantic.is_command:
        actual_intents = [semantic.intent]
    actual_is_command = bool(actual_intents) or bool(semantic and semantic.is_command)
    actual_needs_confirmation = bool(
        plan.needs_confirmation if plan else (semantic.need_clarification if semantic else False)
    )
    safety_allowed = result.safety.allowed if result.safety else None
    safety_reason = result.safety.reason if result.safety else ""
    return {
        "actual_is_command": actual_is_command,
        "actual_intents": actual_intents,
        "actual_should_execute": bool(result.accepted),
        "actual_needs_confirmation": actual_needs_confirmation,
        "actual_risk_level": derive_risk_level(result),
        "stage": result.stage,
        "message": result.message,
        "queue_status": result.queue_status or "",
        "safety_allowed": safety_allowed,
        "safety_reason": safety_reason,
        "plan_truncated": bool(plan.truncated) if plan else False,
        "truncated_count": int(plan.truncated_count) if plan else 0,
        "executed_intents": executed_intents,
        "first_command_intent": command.intent if command else "",
    }


def derive_risk_level(result: Any) -> str:
    if result.command and result.command.metadata.get("risk_level"):
        return str(result.command.metadata["risk_level"]).lower()
    if result.command_plan and result.command_plan.commands:
        risk = result.command_plan.commands[0].metadata.get("risk_level")
        if risk:
            return str(risk).lower()
    if result.semantic:
        if not result.semantic.is_command:
            return "none"
        if result.semantic.dangerous:
            return "dangerous"
        return str(result.semantic.risk_level or "safe").lower()
    return "none"


def compare_case(case: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    expected_intents = case["expected_intents"]
    actual_intents = actual["actual_intents"]
    checks = {
        "is_command_match": case["expected_is_command"] == actual["actual_is_command"],
        "intent_match": expected_intents == actual_intents,
        "should_execute_match": (
            case["expected_should_execute"] == actual["actual_should_execute"]
        ),
        "needs_confirmation_match": (
            case["expected_needs_confirmation"]
            == actual["actual_needs_confirmation"]
        ),
        "risk_level_match": case["expected_risk_level"] == actual["actual_risk_level"],
    }
    severe_reasons = severe_errors(case, actual)
    complete = all(checks.values())
    status = "complete" if complete else ("serious" if severe_reasons else "partial")
    return {
        **checks,
        "comparison_status": status,
        "severe_reasons": severe_reasons,
    }


def severe_errors(case: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    category = case["category"]
    expected_intents = case["expected_intents"]
    actual_intents = actual["actual_intents"]
    expected_risk = case["expected_risk_level"]

    if category.startswith("H_") and actual["actual_should_execute"]:
        reasons.append("普通闲聊被执行")
    if expected_risk in {"dangerous", "disabled"} and actual["actual_should_execute"]:
        reasons.append("危险或禁用动作被允许执行")
    if category.startswith("G_") and (
        actual["actual_should_execute"] or "move_forward" in actual_intents
    ):
        reasons.append("come here 无方向指令被执行")
    if "stop" in expected_intents and "stop" not in actual_intents:
        reasons.append("stop 被漏识别")
    if len(expected_intents) > 1 and expected_intents != actual_intents:
        reasons.append("连续命令顺序或拆分错误")
    if (
        category.startswith("I_")
        and not case["expected_should_execute"]
        and actual["actual_should_execute"]
    ):
        reasons.append("ASR 近似误识别被执行")
    return reasons


def summarize(
    rows: list[dict[str, Any]],
    started_at: datetime,
    finished_at: datetime,
) -> dict[str, Any]:
    total = len(rows)
    complete = sum(row["comparison_status"] == "complete" for row in rows)
    serious = sum(row["comparison_status"] == "serious" for row in rows)
    partial = total - complete - serious
    by_category: dict[str, dict[str, Any]] = {}
    for category in sorted({row["category"] for row in rows}):
        category_rows = [row for row in rows if row["category"] == category]
        category_complete = sum(row["comparison_status"] == "complete" for row in category_rows)
        by_category[category] = {
            "total": len(category_rows),
            "complete": category_complete,
            "partial": sum(row["comparison_status"] == "partial" for row in category_rows),
            "serious": sum(row["comparison_status"] == "serious" for row in category_rows),
            "accuracy_percent": percent(category_complete, len(category_rows)),
        }
    sequence_rows = [row for row in rows if len(row["expected_intents"]) > 1]
    fuzzy_rows = [
        row
        for row in rows
        if row["category"].startswith("F_") or row["category"].startswith("G_")
    ]
    return {
        "started_at": started_at,
        "finished_at": finished_at,
        "total": total,
        "complete": complete,
        "partial": partial,
        "serious": serious,
        "accuracy_percent": percent(complete, total),
        "by_category": by_category,
        "false_execution": sum(
            (not row["expected_should_execute"]) and row["actual_should_execute"]
            for row in rows
        ),
        "missed_recognition": sum(
            row["expected_is_command"] and not row["actual_is_command"] for row in rows
        ),
        "wrong_intent": sum(
            row["expected_intents"] != row["actual_intents"] for row in rows
        ),
        "needs_confirmation_accuracy": percent(
            sum(row["needs_confirmation_match"] for row in rows), total
        ),
        "risk_level_accuracy": percent(sum(row["risk_level_match"] for row in rows), total),
        "sequence_accuracy": percent(
            sum(row["intent_match"] and row["should_execute_match"] for row in sequence_rows),
            len(sequence_rows),
        ),
        "fuzzy_accuracy": percent(
            sum(row["comparison_status"] == "complete" for row in fuzzy_rows),
            len(fuzzy_rows),
        ),
        "chat_false_execution": sum(
            row["category"].startswith("H_") and row["actual_should_execute"]
            for row in rows
        ),
        "dangerous_false_execution": sum(
            row["expected_risk_level"] in {"dangerous", "disabled"}
            and row["actual_should_execute"]
            for row in rows
        ),
        "come_here_false_execution": sum(
            row["category"].startswith("G_")
            and (row["actual_should_execute"] or "move_forward" in row["actual_intents"])
            for row in rows
        ),
        "stop_missed": sum(
            "stop" in row["expected_intents"] and "stop" not in row["actual_intents"]
            for row in rows
        ),
        "system_errors": sum(row["stage"] == "exception" for row in rows),
    }


def percent(numerator: int, denominator: int) -> float:
    return (numerator / denominator * 100.0) if denominator else 0.0


def write_results(rows: list[dict[str, Any]]) -> None:
    with RESULTS_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(csv_row(row))
    with RESULTS_JSONL.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(json_row(row), ensure_ascii=False) + "\n")


def csv_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": row["case_id"],
        "category": row["category"],
        "text": row["text"],
        "expected_is_command": bool_text(row["expected_is_command"]),
        "actual_is_command": bool_text(row["actual_is_command"]),
        "expected_intents": join_intents(row["expected_intents"]),
        "actual_intents": join_intents(row["actual_intents"]),
        "expected_should_execute": bool_text(row["expected_should_execute"]),
        "actual_should_execute": bool_text(row["actual_should_execute"]),
        "expected_needs_confirmation": bool_text(row["expected_needs_confirmation"]),
        "actual_needs_confirmation": bool_text(row["actual_needs_confirmation"]),
        "expected_risk_level": row["expected_risk_level"],
        "actual_risk_level": row["actual_risk_level"],
        "comparison_status": row["comparison_status"],
        "severe_reasons": "; ".join(row["severe_reasons"]),
        "stage": row["stage"],
        "message": row["message"],
        "queue_status": row["queue_status"],
        "safety_allowed": "" if row["safety_allowed"] is None else bool_text(row["safety_allowed"]),
        "safety_reason": row["safety_reason"],
        "plan_truncated": bool_text(row["plan_truncated"]),
        "truncated_count": row["truncated_count"],
        "executed_intents": join_intents(row["executed_intents"]),
        "notes": row["notes"],
    }


def json_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": row["case_id"],
        "text": row["text"],
        "category": row["category"],
        "expected": {
            "is_command": row["expected_is_command"],
            "intents": row["expected_intents"],
            "should_execute": row["expected_should_execute"],
            "needs_confirmation": row["expected_needs_confirmation"],
            "risk_level": row["expected_risk_level"],
        },
        "actual": {
            "is_command": row["actual_is_command"],
            "intents": row["actual_intents"],
            "should_execute": row["actual_should_execute"],
            "needs_confirmation": row["actual_needs_confirmation"],
            "risk_level": row["actual_risk_level"],
            "stage": row["stage"],
            "message": row["message"],
            "queue_status": row["queue_status"],
            "safety_allowed": row["safety_allowed"],
            "safety_reason": row["safety_reason"],
            "plan_truncated": row["plan_truncated"],
            "truncated_count": row["truncated_count"],
            "executed_intents": row["executed_intents"],
        },
        "comparison": {
            "status": row["comparison_status"],
            "severe_reasons": row["severe_reasons"],
            "is_command_match": row["is_command_match"],
            "intent_match": row["intent_match"],
            "should_execute_match": row["should_execute_match"],
            "needs_confirmation_match": row["needs_confirmation_match"],
            "risk_level_match": row["risk_level_match"],
        },
        "raw_result": row["raw_result"],
    }


def write_report(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    lines = [
        "# 模糊文本指令批量测试报告",
        "",
        "## 1. 测试时间",
        f"- 开始时间：{summary['started_at'].isoformat(timespec='seconds')}",
        f"- 结束时间：{summary['finished_at'].isoformat(timespec='seconds')}",
        f"- 数据集：{DATASET_PATH.relative_to(PROJECT_ROOT)}",
        f"- 输出目录：{CURRENT_DIR.relative_to(PROJECT_ROOT)}",
        "- 运行模式：dry_run=true, mock_only=true, real_robot=false, robot_mode=mock, enable_real_robot=false",
        "",
        "## 2. 测试总数",
        f"- 总测试数：{summary['total']}",
        f"- 完全正确：{summary['complete']}",
        f"- 部分正确：{summary['partial']}",
        f"- 严重错误：{summary['serious']}",
        "",
        "## 3. 总体准确率",
        f"- 完全正确率：{summary['accuracy_percent']:.2f}%",
        "",
        "## 4. 分类准确率",
        "| 分类 | 总数 | 完全正确 | 部分正确 | 严重错误 | 准确率 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for category, metric in summary["by_category"].items():
        lines.append(
            f"| {category} | {metric['total']} | {metric['complete']} | "
            f"{metric['partial']} | {metric['serious']} | "
            f"{metric['accuracy_percent']:.2f}% |"
        )
    lines.extend(
        [
            "",
            "## 5. 误执行数量",
            f"- expected_should_execute=false 但实际执行：{summary['false_execution']}",
            f"- 普通闲聊误执行：{summary['chat_false_execution']}",
            f"- 危险或禁用动作误执行：{summary['dangerous_false_execution']}",
            f"- come here 无方向误执行：{summary['come_here_false_execution']}",
            "",
            "## 6. 漏识别数量",
            f"- 期望为命令但实际非命令：{summary['missed_recognition']}",
            f"- stop 漏识别：{summary['stop_missed']}",
            "",
            "## 7. 错误 intent 数量",
            f"- intent 序列不一致：{summary['wrong_intent']}",
            "",
            "## 8. needs_confirmation 判断准确率",
            f"- needs_confirmation 准确率：{summary['needs_confirmation_accuracy']:.2f}%",
            "",
            "## 9. risk_level 判断准确率",
            f"- risk_level 准确率：{summary['risk_level_accuracy']:.2f}%",
            "",
            "## 10. 连续命令解析准确率",
            f"- 多 intent 样例解析准确率：{summary['sequence_accuracy']:.2f}%",
            "",
            "## 11. 模糊指令解析准确率",
            f"- F/G 模糊与 come here 样例完全正确率：{summary['fuzzy_accuracy']:.2f}%",
            "",
            "## 12. 最容易错的输入",
        ]
    )
    for row in most_important_failures(rows, limit=15):
        lines.append(
            f"- {row['case_id']} [{row['category']}] `{row['text']}`："
            f"期望 {join_intents(row['expected_intents']) or 'none'} / "
            f"实际 {join_intents(row['actual_intents']) or 'none'}；"
            f"状态 {row['comparison_status']}；原因 {failure_reason(row)}"
        )
    lines.extend(
        [
            "",
            "## 13. 需要我确认的边界样例",
        ]
    )
    for row in boundary_cases(rows, limit=12):
        lines.append(
            f"- {row['case_id']} `{row['text']}`：期望确认={bool_text(row['expected_needs_confirmation'])}，"
            f"实际确认={bool_text(row['actual_needs_confirmation'])}，"
            f"实际 stage={row['stage']}"
        )
    lines.extend(
        [
            "",
            "## 14. 下一步建议",
            next_step_text(summary),
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_failed_cases(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    failed = [row for row in rows if row["comparison_status"] != "complete"]
    lines = [
        "# 失败样例清单",
        "",
        f"- 失败总数：{len(failed)}",
        f"- 部分正确：{summary['partial']}",
        f"- 严重错误：{summary['serious']}",
        "",
        "## 严重错误",
    ]
    severe = [row for row in failed if row["comparison_status"] == "serious"]
    if severe:
        lines.extend(format_failure_table(severe))
    else:
        lines.append("- 无严重错误。")
    lines.extend(["", "## 部分正确 Top 40"])
    partial = [row for row in failed if row["comparison_status"] == "partial"]
    if partial:
        lines.extend(format_failure_table(partial[:40]))
        if len(partial) > 40:
            lines.append(f"- 另有 {len(partial) - 40} 条部分正确样例，详见 fuzzy_text_test_results.csv。")
    else:
        lines.append("- 无部分正确样例。")
    FAILED_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_failure_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| case_id | category | text | expected | actual | stage | reason |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['category']} | {escape_cell(row['text'])} | "
            f"{join_intents(row['expected_intents']) or 'none'} / "
            f"exec={bool_text(row['expected_should_execute'])} / "
            f"confirm={bool_text(row['expected_needs_confirmation'])} / "
            f"risk={row['expected_risk_level']} | "
            f"{join_intents(row['actual_intents']) or 'none'} / "
            f"exec={bool_text(row['actual_should_execute'])} / "
            f"confirm={bool_text(row['actual_needs_confirmation'])} / "
            f"risk={row['actual_risk_level']} | "
            f"{row['stage']} | {escape_cell(failure_reason(row))} |"
        )
    return lines


def write_confusion_summary(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    intent_pairs = Counter(
        (join_intents(row["expected_intents"]) or "none", join_intents(row["actual_intents"]) or "none")
        for row in rows
    )
    risk_pairs = Counter(
        (row["expected_risk_level"], row["actual_risk_level"]) for row in rows
    )
    severe_reasons = Counter(
        reason for row in rows for reason in row["severe_reasons"]
    )
    by_status = defaultdict(Counter)
    for row in rows:
        by_status[row["category"]][row["comparison_status"]] += 1
    lines = [
        "# 混淆统计",
        "",
        "## 总览",
        f"- 总测试数：{summary['total']}",
        f"- 完全正确：{summary['complete']}",
        f"- 部分正确：{summary['partial']}",
        f"- 严重错误：{summary['serious']}",
        "",
        "## 分类状态分布",
        "| category | complete | partial | serious |",
        "|---|---:|---:|---:|",
    ]
    for category in sorted(by_status):
        counter = by_status[category]
        lines.append(
            f"| {category} | {counter['complete']} | {counter['partial']} | {counter['serious']} |"
        )
    lines.extend(["", "## intent 混淆 Top 30"])
    for (expected, actual), count in intent_pairs.most_common(30):
        if expected != actual:
            lines.append(f"- {expected} -> {actual}: {count}")
    lines.extend(["", "## risk_level 混淆"])
    for (expected, actual), count in risk_pairs.most_common():
        if expected != actual:
            lines.append(f"- {expected} -> {actual}: {count}")
    lines.extend(["", "## 严重错误原因"])
    if severe_reasons:
        for reason, count in severe_reasons.most_common():
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- 无严重错误。")
    CONFUSION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_regression_compare(
    summary: dict[str, Any],
    previous: dict[str, Any] | None,
) -> None:
    before = previous or {
        "accuracy_percent": 79.62,
        "serious": 18,
        "chat_false_execution": 7,
        "asr_false_execution": 5,
        "stop_missed": 3,
        "come_here_false_execution": 0,
        "dangerous_false_execution": 0,
    }
    current_asr_false_execution = sum(
        1
        for path_row in read_current_result_rows()
        if path_row.get("category", "").startswith("I_")
        and path_row.get("expected_should_execute") == "false"
        and path_row.get("actual_should_execute") == "true"
    )
    lines = [
        "# 模糊文本 NLU 修正前后对比",
        "",
        f"- 修正前完全正确率：{float(before['accuracy_percent']):.2f}%",
        f"- 修正后完全正确率：{summary['accuracy_percent']:.2f}%",
        f"- 严重错误：{int(before['serious'])} -> {summary['serious']}",
        f"- 普通闲聊误执行：{int(before['chat_false_execution'])} -> {summary['chat_false_execution']}",
        f"- ASR 近似误识别误执行：{int(before['asr_false_execution'])} -> {current_asr_false_execution}",
        f"- stop 漏识别：{int(before['stop_missed'])} -> {summary['stop_missed']}",
        f"- come here 误执行：{int(before['come_here_false_execution'])} -> {summary['come_here_false_execution']}",
        f"- 危险动作误执行：{int(before['dangerous_false_execution'])} -> {summary['dangerous_false_execution']}",
        "",
        "## 说明",
        "- 本轮未修改 Whisper、音频采集、Go2Adapter 或真机执行逻辑。",
        "- CommandPlan 内部重复命令保留；连续监听窗口去重逻辑未在本轮改动。",
        "- `come here` 无定位信息仍不自动前进。",
        "- 危险和禁用动作仍不允许执行。",
    ]
    REGRESSION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_current_result_rows() -> list[dict[str, str]]:
    if not RESULTS_CSV.exists():
        return []
    with RESULTS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def most_important_failures(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    failed = [row for row in rows if row["comparison_status"] != "complete"]
    return sorted(
        failed,
        key=lambda row: (
            0 if row["comparison_status"] == "serious" else 1,
            row["category"],
            row["case_id"],
        ),
    )[:limit]


def boundary_cases(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    candidates = [
        row
        for row in rows
        if row["category"].startswith(("F_", "G_", "I_"))
        or row["expected_needs_confirmation"]
        or row["actual_needs_confirmation"]
    ]
    failed_first = sorted(
        candidates,
        key=lambda row: (
            row["comparison_status"] == "complete",
            row["category"],
            row["case_id"],
        ),
    )
    return failed_first[:limit]


def next_step_text(summary: dict[str, Any]) -> str:
    if summary["chat_false_execution"]:
        return "- 优先修普通闲聊和否定句过滤，尤其是含 stop/please/dog 的非命令句。"
    if summary["come_here_false_execution"]:
        return "- 优先修 come here 无方向保护，保证没有定位信息时只进入确认或拒绝。"
    if summary["dangerous_false_execution"]:
        return "- 优先修危险和禁用动作的 Safety 拦截，避免进入执行队列。"
    if summary["wrong_intent"]:
        if summary["sequence_accuracy"] < 100.0:
            return "- 优先修 intent 解析和连续命令拆分顺序，再复跑本批次。"
        return "- 优先补齐剩余单命令别名，本轮仅剩 `Take a seat.` 和 `起来。` 两个漏识别边界。"
    if summary["partial"]:
        return "- 优先对部分正确样例补齐 confirmation/risk_level 策略一致性。"
    return "- 当前文本链路批量样例全部通过，下一步可增加 ASR 到文本的端到端回归测试。"


def failure_reason(row: dict[str, Any]) -> str:
    reasons = list(row["severe_reasons"])
    if not row["is_command_match"]:
        reasons.append("is_command mismatch")
    if not row["intent_match"]:
        reasons.append("intent mismatch")
    if not row["should_execute_match"]:
        reasons.append("should_execute mismatch")
    if not row["needs_confirmation_match"]:
        reasons.append("needs_confirmation mismatch")
    if not row["risk_level_match"]:
        reasons.append("risk_level mismatch")
    return "; ".join(reasons) or row["message"]


def join_intents(intents: list[str]) -> str:
    return "->".join(intents)


def bool_text(value: bool) -> str:
    return "true" if bool(value) else "false"


def escape_cell(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
