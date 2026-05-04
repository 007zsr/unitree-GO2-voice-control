from __future__ import annotations

import time
from threading import Event
from typing import Any

from src.models import RobotActionResult, RobotCommand, RobotState
from src.robot.base_adapter import BaseRobotAdapter


class Go2Adapter(BaseRobotAdapter):
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._client = None
        self._state_subscriber = None
        self._connected = False
        self._state = RobotState(connected=False, standing=True, mode="go2")

    def connect(self) -> None:
        network_interface = str(self.config.get("network_interface") or "").strip()
        if not network_interface:
            raise RuntimeError("Go2 network_interface is required for real robot mode")
        domain_id = int(self.config.get("sdk_domain_id", 0))
        try:
            from unitree_sdk2py.core.channel import (  # type: ignore
                ChannelFactoryInitialize,
                ChannelSubscriber,
            )
            from unitree_sdk2py.go2.sport.sport_client import SportClient  # type: ignore
            from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_  # type: ignore

            ChannelFactoryInitialize(domain_id, network_interface)
            self._client = SportClient()
            self._client.SetTimeout(float(self.config.get("connection_timeout_sec", 5)))
            self._client.Init()
            self._connected = True
            self._state.connected = True
            try:
                self._state_subscriber = ChannelSubscriber("rt/sportmodestate", SportModeState_)
                self._state_subscriber.Init()
            except Exception:
                self._state_subscriber = None
        except Exception as exc:
            self._connected = False
            self._state.connected = False
            raise RuntimeError(f"failed to connect Unitree Go2 SDK: {exc}") from exc

    def disconnect(self) -> None:
        try:
            if self._connected:
                self.stop("disconnect")
        finally:
            self._connected = False
            self._state.connected = False
            self._client = None
            self._state_subscriber = None

    def get_state(self) -> RobotState:
        self._state.connected = self._connected
        if not self._connected or self._state_subscriber is None:
            return self._state
        try:
            timeout = float(self.config.get("state_read_timeout_sec", 1))
            sample = self._state_subscriber.Read(timeout=timeout)
            if sample is not None:
                self._state.raw_state = self._object_to_dict(sample)
                self._state.mode = "go2"
        except Exception as exc:
            self._state.raw_state = {"state_read_error": str(exc)}
        return self._state

    def execute(
        self, command: RobotCommand, cancel_event: Event | None = None
    ) -> RobotActionResult:
        if not self._connected or self._client is None:
            return RobotActionResult(False, command.command_id, "Go2 is not connected")
        try:
            if command.intent == "stop":
                return self.stop(command.command_id)
            if command.intent == "stand_up":
                code = self._client.StandUp()
                self._state.standing = True
                return self._result_from_code(command, code, "stand_up")
            if command.intent == "sit_down":
                if hasattr(self._client, "Sit"):
                    code = self._client.Sit()
                else:
                    code = self._client.StandDown()
                self._state.standing = False
                return self._result_from_code(command, code, "sit_down")
            if command.intent == "status_report":
                state = self.get_state()
                return RobotActionResult(True, command.command_id, "status_report", state.to_dict())
            if command.intent in {"move_forward", "move_backward", "turn_left", "turn_right"}:
                return self._execute_velocity(command, cancel_event)
            catalog_result = self._execute_catalog_action(command)
            if catalog_result is not None:
                return catalog_result
            return RobotActionResult(False, command.command_id, f"unknown Go2 command {command.intent}")
        except Exception as exc:
            try:
                self.stop(command.command_id)
            except Exception:
                pass
            return RobotActionResult(
                False,
                command.command_id,
                f"Go2 SDK error: {exc.__class__.__name__}: {exc}",
            )

    def stop(self, command_id: str = "manual_stop") -> RobotActionResult:
        if self._client is None:
            return RobotActionResult(False, command_id, "Go2 client is not initialized")
        try:
            code = self._client.StopMove()
            return RobotActionResult(
                bool(code == 0 or code is None),
                command_id,
                f"Go2 StopMove returned {code}",
                raw_response=code,
            )
        except Exception as exc:
            self._connected = False
            self._state.connected = False
            return RobotActionResult(False, command_id, f"Go2 StopMove failed: {exc}")

    def _execute_velocity(
        self, command: RobotCommand, cancel_event: Event | None
    ) -> RobotActionResult:
        vx = 0.0
        vyaw = 0.0
        speed = command.speed
        if command.intent == "move_forward":
            vx = speed
        elif command.intent == "move_backward":
            vx = -speed
        elif command.intent == "turn_left":
            vyaw = speed
        elif command.intent == "turn_right":
            vyaw = -speed
        code = self._client.Move(vx, 0.0, vyaw)
        if code not in (0, None):
            return self._result_from_code(command, code, command.intent)

        tick = float(self.config.get("motion", {}).get("movement_tick_sec", 0.05))
        deadline = time.monotonic() + command.duration_sec
        while time.monotonic() < deadline:
            if cancel_event and cancel_event.is_set():
                stop_result = self.stop(command.command_id)
                return RobotActionResult(
                    stop_result.success,
                    command.command_id,
                    f"{command.intent} interrupted by stop",
                    raw_response=stop_result.raw_response,
                )
            time.sleep(tick)
        stop_result = self.stop(command.command_id)
        return RobotActionResult(
            stop_result.success,
            command.command_id,
            f"{command.intent} completed and stopped",
            raw_response={"move_code": code, "stop": stop_result.raw_response},
        )

    def _execute_catalog_action(self, command: RobotCommand) -> RobotActionResult | None:
        sdk_method = str(command.metadata.get("sdk_method") or "").strip()
        if not sdk_method:
            return None
        risk_level = str(command.metadata.get("risk_level") or "").lower()
        if risk_level == "dangerous":
            return RobotActionResult(
                False,
                command.command_id,
                "Safety rejected: dangerous action disabled for real robot",
            )
        if not bool(command.metadata.get("real_robot_enabled", False)):
            return RobotActionResult(
                False,
                command.command_id,
                f"Go2 catalog action {command.intent} is not enabled for real robot",
            )
        if self._client is None or not hasattr(self._client, sdk_method):
            return RobotActionResult(
                False,
                command.command_id,
                f"Go2 SDK method {sdk_method!r} is not available",
            )
        method = getattr(self._client, sdk_method)
        args = list(command.metadata.get("sdk_args") or [])
        code = method(*args)
        if command.intent in {"stand_up", "balance_stand", "recovery_stand", "rise_sit"}:
            self._state.standing = True
        elif command.intent in {"sit_down", "stand_down"}:
            self._state.standing = False
        return self._result_from_code(command, code, command.intent)

    def _result_from_code(
        self, command: RobotCommand, code: Any, action_name: str
    ) -> RobotActionResult:
        return RobotActionResult(
            bool(code == 0 or code is None),
            command.command_id,
            f"Go2 {action_name} returned {code}",
            raw_response=code,
        )

    def _object_to_dict(self, value: Any) -> dict[str, Any]:
        if hasattr(value, "__dict__"):
            return {
                key: self._safe_value(item)
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        return {"value": str(value)}

    def _safe_value(self, value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, (list, tuple)):
            return [self._safe_value(item) for item in value[:20]]
        if hasattr(value, "__dict__"):
            return self._object_to_dict(value)
        return str(value)
