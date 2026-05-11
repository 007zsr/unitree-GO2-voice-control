from __future__ import annotations

from typing import Any

from src.config import ConfigSet


REAL_DEMO_ALLOWED_ACTIONS = [
    "stand_up",
    "sit_down",
    "stop",
    "move_forward",
    "move_backward",
    "turn_left",
    "turn_right",
]


def parse_allowed_actions(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def apply_runtime_overrides(configs: ConfigSet, overrides: dict[str, Any] | None) -> None:
    if not overrides:
        return
    real_demo = bool(overrides.get("real_demo", False))
    robot_mode = str(overrides.get("robot_mode") or "").strip()
    if real_demo and not robot_mode:
        robot_mode = "go2"
    if robot_mode:
        configs.app["robot_mode"] = robot_mode
        configs.go2["robot_mode"] = robot_mode

    if bool(overrides.get("enable_real_robot", False)) or real_demo:
        configs.app["enable_real_robot"] = True
        configs.go2["enable_real_robot"] = True

    network_interface = str(overrides.get("interface") or "").strip()
    if network_interface:
        configs.go2["network_interface"] = network_interface

    robot_ip = str(overrides.get("robot_ip") or "").strip()
    if robot_ip:
        configs.go2["robot_ip"] = robot_ip

    allowed_actions = list(overrides.get("allowed_real_actions") or [])
    if real_demo and not allowed_actions:
        allowed_actions = list(REAL_DEMO_ALLOWED_ACTIONS)
    if allowed_actions:
        configs.safety["allowed_real_actions"] = allowed_actions
        configs.safety["allowed_real_actions_reason"] = "action not allowed in real Go2 demo mode"

    if real_demo:
        _apply_real_demo_defaults(configs, allowed_actions)


def _apply_real_demo_defaults(configs: ConfigSet, allowed_actions: list[str]) -> None:
    configs.app["real_demo"] = {
        "enabled": True,
        "allowed_real_actions": allowed_actions,
        "continuous_requires_confirmation": True,
        "continuous_confirm_token": "ENABLE_REAL_CONTINUOUS",
        "dangerous_actions_disabled": True,
    }
    configs.app["log_dir"] = "runtime_data/logs/real_demo"
    configs.app.setdefault("logging", {})["root_dir"] = "runtime_data/logs/real_demo"
    configs.app.setdefault("command_plan", {})["max_commands_per_utterance"] = 1
    configs.go2["prefer_rise_sit_for_stand_up"] = True
    configs.go2["debug_adapter"] = True
    configs.go2["robot_ip"] = str(configs.go2.get("robot_ip") or "192.168.123.161")
    configs.go2.setdefault("motion", {})
    configs.go2["motion"]["movement_tick_sec"] = float(
        configs.go2["motion"].get("movement_tick_sec", 0.05)
    )
    configs.go2["real_demo"] = {
        "max_move_duration_sec": 0.5,
        "max_linear_speed": 0.2,
        "max_yaw_speed": 0.3,
    }
    _apply_real_demo_motion_limits(configs.go2_actions)


def _apply_real_demo_motion_limits(go2_actions: dict[str, Any]) -> None:
    actions = go2_actions.get("actions")
    if not isinstance(actions, dict):
        return
    for intent in ["move_forward", "move_backward"]:
        action = actions.get(intent)
        if isinstance(action, dict):
            action["default_duration_sec"] = 0.5
            action["max_duration_sec"] = 0.5
            action["default_speed"] = 0.2
            action["max_speed"] = 0.2
    for intent in ["turn_left", "turn_right"]:
        action = actions.get(intent)
        if isinstance(action, dict):
            action["default_duration_sec"] = 0.5
            action["max_duration_sec"] = 0.5
            action["default_speed"] = 0.3
            action["max_speed"] = 0.3
