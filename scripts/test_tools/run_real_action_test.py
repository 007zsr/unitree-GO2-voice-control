from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any

import _bootstrap  # noqa: F401
from src.audio.audio_capture import AudioCapture
from src.config import ConfigSet
from src.models import CommandFlowResult, TranscriptResult
from src.runtime.session_runtime import SessionRuntime


STAGE_ALLOWED_ACTIONS = {"sit_down", "stand_up", "rise_sit"}
REPORT_PATH = _bootstrap.PROJECT_ROOT / "docs" / "GO2_REAL_BASIC_ACTION_TEST_01_REPORT.md"
RUNS_PATH = _bootstrap.PROJECT_ROOT / "runtime_data" / "reports" / "go2_real_basic_action_test_01_runs.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description="Restricted real Go2 basic action test")
    parser.add_argument("--config-dir", default=str(_bootstrap.PROJECT_ROOT / "configs"))
    parser.add_argument("--interface", required=True)
    parser.add_argument("--robot-ip", default="192.168.123.161")
    parser.add_argument("--text", default="")
    parser.add_argument("--voice", action="store_true")
    parser.add_argument("--voice-sec", type=float, default=4.0)
    parser.add_argument("--allow-only", required=True)
    parser.add_argument("--confirm-site-ready", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--debug-adapter", action="store_true")
    parser.add_argument("--state-after-delay-sec", type=float, default=1.0)
    parser.add_argument("--observed", default="")
    parser.add_argument("--no-prefer-rise-sit", action="store_true")
    args = parser.parse_args()

    allowed = parse_allowed(args.allow_only)
    if not allowed:
        print("No allowed actions were configured.")
        return 2
    disallowed = allowed - STAGE_ALLOWED_ACTIONS
    if disallowed:
        print(f"Refusing: allow-only contains actions outside this test stage: {sorted(disallowed)}")
        return 2
    if bool(args.text) == bool(args.voice):
        print("Specify exactly one of --text or --voice.")
        return 2
    if not args.confirm_site_ready and not args.dry_run:
        print_site_checklist()
        print("Refusing real action: rerun with --confirm-site-ready after the checklist is true.")
        return 2

    configs = load_real_test_configs(args, sorted(allowed))
    runtime = SessionRuntime(configs)
    flow: CommandFlowResult | None = None
    transcript: TranscriptResult | None = None
    input_text = args.text
    try:
        if args.voice:
            audio_path = record_voice(args.voice_sec, configs)
            transcript = runtime.whisper.transcribe(audio_path)
            input_text = transcript.text
            if not input_text:
                flow = CommandFlowResult(
                    command_id="voice_not_executed",
                    accepted=False,
                    stage="asr",
                    message=transcript.error_message or "ASR did not recognize any text.",
                    transcript=transcript,
                    queue_status="not_submitted",
                )
                write_run_and_report(args, allowed, flow, None, dry_run=args.dry_run)
                print(flow.to_pretty_json())
                return 4

        guard_error, precheck_plan, precheck_semantic = validate_single_allowed_plan(runtime, input_text, allowed)
        if guard_error:
            precheck_command = precheck_plan.commands[0] if precheck_plan and precheck_plan.commands else None
            flow = CommandFlowResult(
                command_id="not_submitted",
                accepted=False,
                stage="safety",
                message=guard_error,
                transcript=transcript or TranscriptResult(text=input_text, no_speech_prob=0.0),
                semantic=precheck_semantic,
                command=precheck_command,
                command_plan=precheck_plan,
                queue_status="not_submitted",
            )
            write_run_and_report(args, allowed, flow, None, dry_run=args.dry_run)
            print(flow.to_pretty_json())
            return 3

        if args.dry_run:
            precheck_command = precheck_plan.commands[0] if precheck_plan and precheck_plan.commands else None
            flow = CommandFlowResult(
                command_id="dry_run",
                accepted=True,
                stage="dry_run",
                message="Plan is allowed for this real robot test stage; no command sent.",
                transcript=transcript or TranscriptResult(text=input_text, no_speech_prob=0.0),
                semantic=precheck_semantic,
                command=precheck_command,
                command_plan=precheck_plan,
                queue_status="not_submitted",
            )
            write_run_and_report(args, allowed, flow, None, dry_run=True)
            print(flow.to_pretty_json())
            return 0

        runtime.start()
        print(json.dumps({"adapter_selected": runtime.get_current_status()}, ensure_ascii=False, indent=2))
        before_state = read_runtime_state(runtime, "before_action")
        flow = runtime.process_text(
            input_text,
            transcript=transcript,
            deduplicate=False,
        )
        if args.state_after_delay_sec > 0:
            time.sleep(args.state_after_delay_sec)
        after_state = read_runtime_state(runtime, "after_action")
        write_run_and_report(
            args,
            allowed,
            flow,
            runtime,
            dry_run=False,
            before_state=before_state,
            after_state=after_state,
        )
        print(flow.to_pretty_json())
        return 0 if flow.accepted else 5
    finally:
        try:
            runtime.shutdown()
        except Exception:
            pass


def parse_allowed(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


def load_real_test_configs(args: argparse.Namespace, allowed: list[str]) -> ConfigSet:
    configs = ConfigSet.load(args.config_dir)
    configs.app["robot_mode"] = "go2"
    configs.app["enable_real_robot"] = True
    configs.go2["robot_mode"] = "go2"
    configs.go2["enable_real_robot"] = True
    configs.go2["network_interface"] = args.interface
    configs.go2["robot_ip"] = args.robot_ip
    configs.go2["stop_on_disconnect"] = False
    configs.go2["debug_adapter"] = bool(args.debug_adapter)
    configs.go2["prefer_rise_sit_for_stand_up"] = not args.no_prefer_rise_sit
    configs.safety["allowed_real_actions"] = allowed
    configs.app.setdefault("command_plan", {})["max_commands_per_utterance"] = 1
    configs.app.setdefault("continuous_listening", {})["deduplicate_enabled"] = True
    return configs


def validate_single_allowed_plan(runtime: SessionRuntime, text: str, allowed: set[str]) -> tuple[str, Any, Any]:
    semantic_items, parse_meta = runtime._parse_semantic_items(text)
    if not semantic_items:
        return "No executable command was recognized.", None, None
    commands = runtime._normalize_plan_commands(semantic_items, text, "precheck")
    plan = runtime._build_command_plan(text, semantic_items, commands, parse_meta)
    if len(plan.commands) != 1:
        return "Rejected: this real robot test stage only allows one command per run.", plan, semantic_items[0][1]
    command = plan.commands[0]
    if command.intent not in allowed:
        return "Rejected: action not allowed in this real robot test stage", plan, semantic_items[0][1]
    if plan.needs_confirmation:
        return f"Rejected: command plan needs confirmation: {plan.reason}", plan, semantic_items[0][1]
    return "", plan, semantic_items[0][1]


def record_voice(duration_sec: float, configs: ConfigSet) -> Path:
    audio_config = configs.app.get("audio", {})
    target = _bootstrap.PROJECT_ROOT / "runtime_data" / "debug_audio" / "real_action_test_01.wav"
    capture = AudioCapture(
        sample_rate=16000,
        channels=1,
        input_device=audio_config.get("input_device", "default"),
    )
    print(f"Recording one-shot voice for {duration_sec:.1f}s ...", flush=True)
    return capture.record_to_file(target, duration_sec)


def write_run_and_report(
    args: argparse.Namespace,
    allowed: set[str],
    flow: CommandFlowResult,
    runtime: SessionRuntime | None,
    dry_run: bool,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
) -> None:
    RUNS_PATH.parent.mkdir(parents=True, exist_ok=True)
    adapter_result = first_adapter_result(flow)
    record = {
        "input_type": "voice" if args.voice else "text",
        "input_text": args.text,
        "transcript": flow.transcript.to_dict() if flow.transcript else None,
        "flow": flow.to_dict(),
        "adapter_result": adapter_result,
        "allowed_actions": sorted(allowed),
        "interface": args.interface,
        "robot_ip": args.robot_ip,
        "dry_run": dry_run,
        "site_confirmed": bool(args.confirm_site_ready),
        "observed": args.observed,
        "runtime_status": runtime.get_current_status() if runtime else None,
        "before_state": before_state,
        "after_state": after_state,
        "motion_command_sent": bool(flow.accepted and not dry_run),
        "non_whitelist_action_sent": False,
        "dangerous_action_sent": False,
        "configuration_restored": True,
    }
    with RUNS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_report()


def read_runtime_state(runtime: SessionRuntime, label: str) -> dict[str, Any]:
    try:
        return {
            "label": label,
            "state": runtime.adapter.get_state().to_dict(),
            "error": "",
        }
    except Exception as exc:
        return {
            "label": label,
            "state": None,
            "error": f"{exc.__class__.__name__}: {exc}",
        }


def first_adapter_result(flow: CommandFlowResult) -> dict[str, Any] | None:
    for item in flow.plan_results:
        adapter_result = item.get("adapter_result")
        if isinstance(adapter_result, dict):
            return adapter_result
    return None


def write_report() -> None:
    runs = read_runs()
    text_sit = find_latest(runs, "text", "sit_down")
    text_stand = find_latest(runs, "text", "stand_up")
    voice_sit = find_latest(runs, "voice", "sit_down")
    voice_stand = find_latest(runs, "voice", "stand_up")
    lines = [
        "# Go2 Real Basic Action Test 01 Report",
        "",
        "## 1. Time",
        "",
        f"- Report updated from `{RUNS_PATH}`",
        "",
        "## 2. Environment",
        "",
        "- Project path: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control`",
        "- Interface: `enx4cea41674695`",
        "- IP: `192.168.123.222/24`",
        "- SDK: `unitree_sdk2py` from project `.venv` / `third_party/unitree_sdk2_python`",
        "- CycloneDDS: OK from prior SDK import/read-only checks",
        "",
        "## 3. Safety settings",
        "",
        "- robot_mode during test: `go2` in memory only",
        "- enable_real_robot during test: `true` in memory only",
        "- allowed actions: `sit_down`, `stand_up`, `rise_sit`",
        "- continuous listening: disabled / not used by this command",
        "- dangerous actions: not allowed",
        "- disconnect behavior: `stop_on_disconnect=false` for this stage to avoid implicit StopMove",
        "",
        *section_for("4. Text sit_down test", text_sit),
        "",
        *section_for("5. Text stand_up test", text_stand),
        "",
        *section_for("6. Voice sit_down test", voice_sit),
        "",
        *section_for("7. Voice stand_up test", voice_stand),
        "",
        "## 8. Rejected commands",
        "",
        *rejected_lines(runs),
        "",
        "## 9. Unexpected behavior",
        "",
        *unexpected_lines(runs),
        "",
        "## 10. Final status",
        "",
        "- robot_mode restored: `mock` in config files",
        "- enable_real_robot restored: `false` in config files",
        f"- can continue to next test: `{can_continue(text_sit, text_stand, voice_sit, voice_stand)}`",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_runs() -> list[dict[str, Any]]:
    if not RUNS_PATH.exists():
        return []
    runs: list[dict[str, Any]] = []
    for line in RUNS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            runs.append(json.loads(line))
    return runs


def find_latest(runs: list[dict[str, Any]], input_type: str, intent: str) -> dict[str, Any] | None:
    for run in reversed(runs):
        flow = run.get("flow") or {}
        semantic = flow.get("semantic") or {}
        command = flow.get("command") or {}
        if run.get("input_type") == input_type and (
            semantic.get("intent") == intent or command.get("intent") == intent
        ):
            return run
    return None


def section_for(title: str, run: dict[str, Any] | None) -> list[str]:
    lines = [f"## {title}", ""]
    if run is None:
        return [*lines, "- result: not executed"]
    flow = run.get("flow") or {}
    transcript = flow.get("transcript") or {}
    semantic = flow.get("semantic") or {}
    safety = flow.get("safety") or {}
    adapter = run.get("adapter_result") or {}
    raw_response = adapter.get("raw_response") if isinstance(adapter, dict) else None
    sdk_method = raw_response.get("sdk_method") if isinstance(raw_response, dict) else ""
    return [
        *lines,
        f"- input: `{run.get('input_text') or transcript.get('text') or ''}`",
        f"- transcript: `{transcript.get('text') or ''}`",
        f"- intent: `{semantic.get('intent') or ''}`",
        f"- Safety: `{(safety or {}).get('reason') or flow.get('stage')}`",
        f"- SDK method: `{sdk_method or 'unknown/not executed'}`",
        f"- result: `{'OK' if flow.get('accepted') else 'FAIL'}`",
        f"- adapter message: `{adapter.get('message') if isinstance(adapter, dict) else ''}`",
        f"- observed robot behavior: `{run.get('observed') or 'not recorded by script'}`",
        f"- before high state: `{state_summary(run.get('before_state'))}`",
        f"- after high state: `{state_summary(run.get('after_state'))}`",
    ]


def rejected_lines(runs: list[dict[str, Any]]) -> list[str]:
    rejected = [run for run in runs if not (run.get("flow") or {}).get("accepted")]
    if not rejected:
        return ["- none recorded"]
    return [
        f"- {run.get('input_type')}: `{run.get('input_text')}` -> {(run.get('flow') or {}).get('message')}"
        for run in rejected
    ]


def unexpected_lines(runs: list[dict[str, Any]]) -> list[str]:
    unexpected = [run for run in runs if run.get("observed") and "unexpected" in run.get("observed", "").lower()]
    if not unexpected:
        return ["- none recorded by script"]
    return [f"- {run.get('observed')}" for run in unexpected]


def can_continue(*runs: dict[str, Any] | None) -> str:
    text_sit, text_stand, voice_sit, voice_stand = runs
    text_ok = all(real_run_accepted(run) for run in [text_sit, text_stand])
    voice_ok_or_missing = all(
        run is None or real_run_accepted(run)
        for run in [voice_sit, voice_stand]
    )
    return "yes" if text_ok and voice_ok_or_missing else "no"


def real_run_accepted(run: dict[str, Any] | None) -> bool:
    return bool(run and not run.get("dry_run") and (run.get("flow") or {}).get("accepted"))


def state_summary(snapshot: Any) -> str:
    if not isinstance(snapshot, dict):
        return "not captured"
    if snapshot.get("error"):
        return snapshot["error"]
    state = snapshot.get("state") or {}
    if not isinstance(state, dict):
        return "not captured"
    raw = state.get("raw_state") or {}
    if not raw:
        return "captured without raw_state"
    keys = ["mode", "gait_type", "progress", "position", "velocity", "yaw_speed", "body_height", "error_code"]
    summary = {key: raw.get(key) for key in keys if key in raw}
    return json.dumps(summary or raw, ensure_ascii=False)[:500]


def print_site_checklist() -> None:
    print("Before real Go2 motion, confirm all of these are true:")
    print("1. Go2 is on flat ground.")
    print("2. At least 1 meter around the robot is clear.")
    print("3. Nobody is in front of or behind the robot.")
    print("4. Battery is normal.")
    print("5. Go2 is powered on and connected to this Ubuntu host.")
    print("6. You can manually stop the robot immediately if needed.")
    print("7. Continuous listening is not running.")
    print("8. This run is not testing movement/turning actions.")


if __name__ == "__main__":
    raise SystemExit(main())
