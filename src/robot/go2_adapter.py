from __future__ import annotations

import json
import os
import time
from pathlib import Path
from threading import Event
from typing import Any

from src.models import RobotActionResult, RobotCommand, RobotState, utc_now_iso
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
        self._debug_log("Go2Adapter.connect START", request_args={"network_interface": network_interface})
        if not network_interface:
            self._debug_log("Go2Adapter.connect END", success=False, error="missing network_interface")
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
            self._debug_log("Go2Adapter.connect END", success=True, state_subscriber_initialized=self._state_subscriber is not None)
        except Exception as exc:
            self._connected = False
            self._state.connected = False
            self._debug_log(
                "Go2Adapter.connect END",
                success=False,
                error=f"{exc.__class__.__name__}: {exc}",
            )
            raise RuntimeError(f"failed to connect Unitree Go2 SDK: {exc}") from exc

    def disconnect(self) -> None:
        try:
            self._debug_log(
                "Go2Adapter.disconnect START",
                stop_on_disconnect=bool(self.config.get("stop_on_disconnect", True)),
            )
            if self._connected and bool(self.config.get("stop_on_disconnect", True)):
                self.stop("disconnect")
        finally:
            self._connected = False
            self._state.connected = False
            self._client = None
            self._state_subscriber = None
            self._debug_log("Go2Adapter.disconnect END")

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
        self._debug_log(
            "Go2Adapter.execute START",
            command_id=command.command_id,
            intent=command.intent,
            request_args={
                "duration_sec": command.duration_sec,
                "speed": command.speed,
                "speed_level": command.speed_level,
                "metadata_sdk_method": command.metadata.get("sdk_method"),
                "metadata_sdk_args": command.metadata.get("sdk_args"),
            },
        )
        if not self._connected or self._client is None:
            return self._finish_execute(
                command,
                RobotActionResult(False, command.command_id, "Go2 is not connected"),
            )
        try:
            if command.intent == "stop":
                return self._finish_execute(command, self.stop(command.command_id))
            if command.intent == "stand_up":
                sdk_method = "StandUp"
                if bool(self.config.get("prefer_rise_sit_for_stand_up", False)) and hasattr(
                    self._client, "RiseSit"
                ):
                    sdk_method = "RiseSit"
                    self._debug_log(
                        "Go2Adapter.sdk_call START",
                        command_id=command.command_id,
                        intent=command.intent,
                        sdk_method=sdk_method,
                        request_args=[],
                    )
                    code = self._client.RiseSit()
                else:
                    self._debug_log(
                        "Go2Adapter.sdk_call START",
                        command_id=command.command_id,
                        intent=command.intent,
                        sdk_method=sdk_method,
                        request_args=[],
                    )
                    code = self._client.StandUp()
                self._debug_log(
                    "Go2Adapter.sdk_call END",
                    command_id=command.command_id,
                    intent=command.intent,
                    sdk_method=sdk_method,
                    sdk_return_code=code,
                    sdk_return_message=self._sdk_message(code),
                )
                self._state.standing = True
                return self._finish_execute(
                    command,
                    self._result_from_code(command, code, "stand_up", sdk_method=sdk_method),
                )
            if command.intent == "sit_down":
                sdk_method = "Sit"
                if hasattr(self._client, "Sit"):
                    self._debug_log(
                        "Go2Adapter.sdk_call START",
                        command_id=command.command_id,
                        intent=command.intent,
                        sdk_method=sdk_method,
                        request_args=[],
                    )
                    code = self._client.Sit()
                else:
                    sdk_method = "StandDown"
                    self._debug_log(
                        "Go2Adapter.sdk_call START",
                        command_id=command.command_id,
                        intent=command.intent,
                        sdk_method=sdk_method,
                        request_args=[],
                    )
                    code = self._client.StandDown()
                self._debug_log(
                    "Go2Adapter.sdk_call END",
                    command_id=command.command_id,
                    intent=command.intent,
                    sdk_method=sdk_method,
                    sdk_return_code=code,
                    sdk_return_message=self._sdk_message(code),
                )
                self._state.standing = False
                return self._finish_execute(
                    command,
                    self._result_from_code(command, code, "sit_down", sdk_method=sdk_method),
                )
            if command.intent == "status_report":
                state = self.get_state()
                return self._finish_execute(
                    command,
                    RobotActionResult(True, command.command_id, "status_report", state.to_dict()),
                )
            if command.intent in {"move_forward", "move_backward", "turn_left", "turn_right"}:
                return self._finish_execute(command, self._execute_velocity(command, cancel_event))
            catalog_result = self._execute_catalog_action(command)
            if catalog_result is not None:
                return self._finish_execute(command, catalog_result)
            return self._finish_execute(
                command,
                RobotActionResult(False, command.command_id, f"unknown Go2 command {command.intent}"),
            )
        except Exception as exc:
            if bool(self.config.get("stop_on_sdk_exception", True)):
                try:
                    self.stop(command.command_id)
                except Exception:
                    pass
            return self._finish_execute(
                command,
                RobotActionResult(
                    False,
                    command.command_id,
                    f"Go2 SDK error: {exc.__class__.__name__}: {exc}",
                ),
            )

    def stop(self, command_id: str = "manual_stop") -> RobotActionResult:
        if self._client is None:
            return RobotActionResult(False, command_id, "Go2 client is not initialized")
        try:
            self._debug_log(
                "Go2Adapter.sdk_call START",
                command_id=command_id,
                intent="stop",
                sdk_method="StopMove",
                request_args=[],
            )
            code = self._client.StopMove()
            self._debug_log(
                "Go2Adapter.sdk_call END",
                command_id=command_id,
                intent="stop",
                sdk_method="StopMove",
                sdk_return_code=code,
                sdk_return_message=self._sdk_message(code),
            )
            return RobotActionResult(
                bool(code == 0 or code is None),
                command_id,
                f"Go2 StopMove returned {code}",
                raw_response={"sdk_method": "StopMove", "code": code},
            )
        except Exception as exc:
            self._connected = False
            self._state.connected = False
            self._debug_log(
                "Go2Adapter.sdk_call END",
                command_id=command_id,
                intent="stop",
                sdk_method="StopMove",
                sdk_return_code=None,
                sdk_return_message=f"{exc.__class__.__name__}: {exc}",
            )
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
        args = [vx, 0.0, vyaw]
        self._debug_log(
            "Go2Adapter.sdk_call START",
            command_id=command.command_id,
            intent=command.intent,
            sdk_method="Move",
            request_args=args,
        )
        code = self._client.Move(*args)
        self._debug_log(
            "Go2Adapter.sdk_call END",
            command_id=command.command_id,
            intent=command.intent,
            sdk_method="Move",
            request_args=args,
            sdk_return_code=code,
            sdk_return_message=self._sdk_message(code),
        )
        if code not in (0, None):
            return self._result_from_code(command, code, command.intent, sdk_method="Move")

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
            raw_response={"sdk_method": "Move", "code": code, "stop": stop_result.raw_response},
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
        self._debug_log(
            "Go2Adapter.sdk_call START",
            command_id=command.command_id,
            intent=command.intent,
            sdk_method=sdk_method,
            request_args=args,
        )
        code = method(*args)
        self._debug_log(
            "Go2Adapter.sdk_call END",
            command_id=command.command_id,
            intent=command.intent,
            sdk_method=sdk_method,
            request_args=args,
            sdk_return_code=code,
            sdk_return_message=self._sdk_message(code),
        )
        if command.intent in {"stand_up", "balance_stand", "recovery_stand", "rise_sit"}:
            self._state.standing = True
        elif command.intent in {"sit_down", "stand_down"}:
            self._state.standing = False
        return self._result_from_code(command, code, command.intent, sdk_method=sdk_method)

    def _result_from_code(
        self,
        command: RobotCommand,
        code: Any,
        action_name: str,
        sdk_method: str | None = None,
    ) -> RobotActionResult:
        method_text = f" via {sdk_method}" if sdk_method else ""
        raw_response: Any = {"sdk_method": sdk_method, "code": code} if sdk_method else code
        return RobotActionResult(
            bool(code == 0 or code is None),
            command.command_id,
            f"Go2 {action_name}{method_text} returned {code}",
            raw_response=raw_response,
        )

    def _finish_execute(self, command: RobotCommand, result: RobotActionResult) -> RobotActionResult:
        raw_response = result.raw_response if isinstance(result.raw_response, dict) else {}
        sdk_method = raw_response.get("sdk_method") if isinstance(raw_response, dict) else None
        code = raw_response.get("code") if isinstance(raw_response, dict) else result.raw_response
        self._debug_log(
            "Go2Adapter.execute END",
            command_id=command.command_id,
            intent=command.intent,
            sdk_method=sdk_method,
            sdk_return_code=code,
            sdk_return_message=result.message,
            success=result.success,
            result=result.to_dict(),
        )
        return result

    def _sdk_message(self, code: Any) -> str:
        if code == 0:
            return "OK"
        if code is None:
            return "OK/No reply"
        return f"SDK returned {code}"

    def _debug_enabled(self) -> bool:
        if os.environ.get("GO2_ADAPTER_DEBUG", "").lower() in {"1", "true", "yes"}:
            return True
        return bool(self.config.get("debug_adapter", True))

    def _debug_log(self, event: str, **fields: Any) -> None:
        if not self._debug_enabled():
            return
        payload: dict[str, Any] = {
            "timestamp": utc_now_iso(),
            "event": event,
            "interface": str(self.config.get("network_interface") or ""),
            "robot_mode": str(self.config.get("robot_mode") or "go2"),
            "enable_real_robot": bool(self.config.get("enable_real_robot", False)),
            "sport_client_initialized": self._client is not None,
            "connected": self._connected,
        }
        payload.update(fields)
        log_dir = Path(__file__).resolve().parents[2] / "runtime_data" / "logs" / "go2_adapter_debug"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "go2_adapter_debug.jsonl"
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(self._json_safe(payload), ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._json_safe(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

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
