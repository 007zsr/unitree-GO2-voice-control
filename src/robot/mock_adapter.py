from __future__ import annotations

import time
from threading import Event

from src.commands.command_catalog import CommandCatalog
from src.models import RobotActionResult, RobotCommand, RobotState
from src.robot.base_adapter import BaseRobotAdapter


class MockAdapter(BaseRobotAdapter):
    def __init__(self, catalog: CommandCatalog | None = None):
        self.catalog = catalog
        self.state = RobotState(connected=False, standing=True, mode="mock")
        self.executed: list[RobotCommand] = []
        self._moving = False

    def connect(self) -> None:
        self.state.connected = True
        self.state.mode = "mock"

    def disconnect(self) -> None:
        self._moving = False
        self.state.connected = False

    def get_state(self) -> RobotState:
        return self.state

    def execute(
        self, command: RobotCommand, cancel_event: Event | None = None
    ) -> RobotActionResult:
        self.executed.append(command)
        if command.intent == "stop":
            return self.stop(command.command_id)
        if command.intent == "stand_up":
            self.state.standing = True
            return RobotActionResult(True, command.command_id, "mock stand_up completed")
        if command.intent in {"sit_down", "stand_down"}:
            self.state.standing = False
            return RobotActionResult(True, command.command_id, f"mock {command.intent} completed")
        if command.intent in {"balance_stand", "recovery_stand", "rise_sit"}:
            self.state.standing = True
            return RobotActionResult(True, command.command_id, f"mock {command.intent} completed")
        if command.intent == "status_report":
            return RobotActionResult(
                True,
                command.command_id,
                "mock status reported",
                raw_response=self.state.to_dict(),
            )
        if command.intent in {"move_forward", "move_backward", "turn_left", "turn_right"}:
            self._moving = True
            deadline = time.monotonic() + command.duration_sec
            while time.monotonic() < deadline:
                if cancel_event and cancel_event.is_set():
                    self._moving = False
                    return RobotActionResult(
                        True,
                        command.command_id,
                        f"mock {command.intent} interrupted by stop",
                    )
                time.sleep(0.02)
            self._moving = False
            return RobotActionResult(True, command.command_id, f"mock {command.intent} completed")
        if self._is_catalog_action(command):
            return RobotActionResult(
                True,
                command.command_id,
                f"Mock: {command.intent} simulated",
                raw_response={
                    "intent": command.intent,
                    "official_name": command.metadata.get("official_name"),
                    "sdk_method": command.metadata.get("sdk_method"),
                    "risk_level": command.metadata.get("risk_level"),
                },
            )
        return RobotActionResult(False, command.command_id, f"mock unknown command {command.intent}")

    def stop(self, command_id: str = "manual_stop") -> RobotActionResult:
        self._moving = False
        return RobotActionResult(True, command_id, "mock stop completed")

    def _is_catalog_action(self, command: RobotCommand) -> bool:
        if command.metadata.get("mock_enabled") is False:
            return False
        if command.metadata.get("sdk_method") or command.metadata.get("official_name"):
            return True
        return bool(self.catalog and self.catalog.get(command.intent))
