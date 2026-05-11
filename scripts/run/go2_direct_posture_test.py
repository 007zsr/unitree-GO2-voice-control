from __future__ import annotations

import argparse
import json
import time
from typing import Any

import _bootstrap  # noqa: F401


CONFIRM_PHRASE = "I_UNDERSTAND_THIS_WILL_CONTROL_GO2"
ACTION_METHODS = {
    "sit": "Sit",
    "rise": "RiseSit",
    "standup": "StandUp",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded direct Unitree Go2 posture diagnostic. This sends one posture command."
    )
    parser.add_argument("--interface", required=True)
    parser.add_argument("--action", required=True, choices=sorted(ACTION_METHODS))
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--domain-id", type=int, default=0)
    parser.add_argument("--timeout-sec", type=float, default=5.0)
    parser.add_argument("--state-timeout-sec", type=float, default=1.0)
    parser.add_argument("--after-delay-sec", type=float, default=1.0)
    args = parser.parse_args()

    if args.confirm != CONFIRM_PHRASE:
        print(
            json.dumps(
                {
                    "accepted": False,
                    "reason": f"confirmation phrase must be exactly {CONFIRM_PHRASE!r}",
                    "motion_command_sent": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    sdk_method = ACTION_METHODS[args.action]
    result: dict[str, Any] = {
        "accepted": True,
        "interface": args.interface,
        "domain_id": args.domain_id,
        "action": args.action,
        "sdk_method": sdk_method,
        "allowed_methods": sorted(ACTION_METHODS.values()),
        "motion_command_sent": False,
        "dangerous_action_sent": False,
    }

    try:
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
        from unitree_sdk2py.go2.sport.sport_client import SportClient
        from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_

        ChannelFactoryInitialize(args.domain_id, args.interface)
        subscriber = ChannelSubscriber("rt/sportmodestate", SportModeState_)
        subscriber.Init()
        result["before_high_state"] = read_state(subscriber, args.state_timeout_sec)

        client = SportClient()
        client.SetTimeout(args.timeout_sec)
        client.Init()
        method = getattr(client, sdk_method)
        result["motion_command_sent"] = True
        code = method()
        result["sdk_return_code"] = code
        result["sdk_return_message"] = sdk_message(code)

        if args.after_delay_sec > 0:
            time.sleep(args.after_delay_sec)
        result["after_high_state"] = read_state(subscriber, args.state_timeout_sec)
        print(json.dumps(json_safe(result), ensure_ascii=False, indent=2))
        return 0 if code in (0, None) else 4
    except Exception as exc:
        result["error"] = f"{exc.__class__.__name__}: {exc}"
        print(json.dumps(json_safe(result), ensure_ascii=False, indent=2))
        return 5


def read_state(subscriber: Any, timeout_sec: float) -> dict[str, Any]:
    try:
        sample = subscriber.Read(timeout=timeout_sec)
        if sample is None:
            return {"status": "NO_SAMPLE"}
        return {
            "status": "OK",
            "mode": safe_value(getattr(sample, "mode", None)),
            "gait_type": safe_value(getattr(sample, "gait_type", None)),
            "progress": safe_value(getattr(sample, "progress", None)),
            "position": safe_value(getattr(sample, "position", None)),
            "velocity": safe_value(getattr(sample, "velocity", None)),
            "yaw_speed": safe_value(getattr(sample, "yaw_speed", None)),
            "body_height": safe_value(getattr(sample, "body_height", None)),
            "error_code": safe_value(getattr(sample, "error_code", None)),
        }
    except Exception as exc:
        return {"status": "FAIL", "error": f"{exc.__class__.__name__}: {exc}"}


def sdk_message(code: Any) -> str:
    if code == 0:
        return "OK"
    if code is None:
        return "OK/No reply"
    return f"SDK returned {code}"


def safe_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [safe_value(item) for item in value[:20]]
    try:
        if hasattr(value, "__iter__"):
            return [safe_value(item) for item in list(value)[:20]]
    except Exception:
        pass
    return str(value)


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
