from __future__ import annotations

from typing import Any

from src.commands.command_catalog import CommandCatalog
from src.models import RobotCommand, RobotState, SafetyDecision, SemanticResult


class SafetyController:
    MOTION_INTENTS = {"move_forward", "move_backward", "turn_left", "turn_right"}

    def __init__(
        self,
        config: dict[str, Any],
        catalog: CommandCatalog,
        robot_mode: str = "mock",
        enable_real_robot: bool = False,
    ):
        self.config = config
        self.catalog = catalog
        self.robot_mode = robot_mode
        self.enable_real_robot = enable_real_robot

    def check(
        self,
        semantic: SemanticResult,
        command: RobotCommand,
        robot_state: RobotState,
    ) -> SafetyDecision:
        if command.intent == "stop":
            return SafetyDecision(True, "stop has highest priority", command)

        if bool(self.config.get("reject_need_clarification", True)) and semantic.need_clarification:
            return SafetyDecision(False, "semantic result needs clarification", command)

        spec = self.catalog.get(command.intent)
        if (
            bool(self.config.get("reject_dangerous_semantics", True))
            and semantic.dangerous
            and not (spec and spec.risk_level == "dangerous")
        ):
            return SafetyDecision(False, "semantic result marked request as dangerous", command)

        min_confidence = float(self.config.get("min_semantic_confidence", 0.65))
        if semantic.confidence < min_confidence:
            return SafetyDecision(
                False,
                f"semantic confidence {semantic.confidence:.2f} below {min_confidence:.2f}",
                command,
            )

        if spec is None:
            return SafetyDecision(False, "command intent is not whitelisted", command)

        risk_level = str(
            command.metadata.get("risk_level")
            or semantic.risk_level
            or spec.risk_level
            or "safe"
        ).lower()
        if bool(command.metadata.get("rejected_by_nlu")) or semantic.rejected_by_nlu:
            return SafetyDecision(False, "catalog action was rejected by NLU policy", command)
        if risk_level == "disabled":
            return SafetyDecision(False, "disabled catalog action cannot execute", command)
        if not bool(spec.mock_enabled) and self.robot_mode != "go2":
            return SafetyDecision(False, "catalog action is disabled for mock execution", command)
        if self.robot_mode == "go2":
            if risk_level == "dangerous":
                return SafetyDecision(False, "dangerous action disabled for real robot", command)
            if risk_level == "caution" and not bool(
                self.config.get("allow_caution_actions_on_real_robot", False)
            ):
                return SafetyDecision(False, "caution action disabled for real robot by default", command)
            if not bool(spec.real_robot_enabled):
                return SafetyDecision(False, "catalog action is not enabled for real robot", command)
        if self.robot_mode == "go2" and not self.enable_real_robot:
            return SafetyDecision(False, "real robot mode is disabled by configuration", command)

        if self.robot_mode == "go2" and not robot_state.connected:
            if command.intent == "status_report" and bool(
                self.config.get("allow_status_without_connection", True)
            ):
                return SafetyDecision(True, "status report allowed without connection", command)
            return SafetyDecision(False, "Go2 is not connected", command)

        if (
            command.intent in self.MOTION_INTENTS
            and bool(self.config.get("require_connected_for_motion", True))
            and not robot_state.connected
        ):
            return SafetyDecision(False, "robot is not connected for motion command", command)

        allowed_levels = set(self.config.get("allowed_speed_levels", ["slow"]))
        if (
            bool(self.config.get("reject_fast_speed_request", True))
            and command.speed_level not in allowed_levels
        ):
            return SafetyDecision(False, f"speed level {command.speed_level!r} is not allowed", command)

        if spec.requires_duration and command.duration_sec <= 0:
            return SafetyDecision(False, "duration must be positive", command)

        if spec.max_duration_sec and command.duration_sec > spec.max_duration_sec:
            return SafetyDecision(
                False,
                f"duration {command.duration_sec:.2f}s exceeds max {spec.max_duration_sec:.2f}s",
                command,
            )

        if command.speed > spec.max_speed:
            return SafetyDecision(
                False,
                f"speed {command.speed:.2f} exceeds max {spec.max_speed:.2f}",
                command,
            )

        if spec.requires_robot_standing and not robot_state.standing:
            return SafetyDecision(False, "robot must be standing before this action", command)

        return SafetyDecision(True, "allowed", command)
