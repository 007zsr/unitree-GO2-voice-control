from __future__ import annotations

import argparse
import json
import subprocess
import time
from typing import Any

import _bootstrap  # noqa: F401
from src.config import ConfigSet


HIGH_STATE_TOPIC = "rt/sportmodestate"
WIRELESS_TOPIC = "rt/wirelesscontroller"


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Unitree Go2 SDK2 connection check")
    parser.add_argument("--config-dir", default=str(_bootstrap.PROJECT_ROOT / "configs"))
    parser.add_argument("--interface", required=True, help="Network interface connected to Go2")
    parser.add_argument("--domain-id", type=int, default=0)
    parser.add_argument("--timeout-sec", type=float, default=2.0)
    parser.add_argument("--samples", type=int, default=3)
    args = parser.parse_args()

    configs = ConfigSet.load(args.config_dir)
    result: dict[str, Any] = {
        "interface": args.interface,
        "domain_id": args.domain_id,
        "robot_mode": configs.robot_mode,
        "enable_real_robot": configs.enable_real_robot,
        "motion_command_sent": False,
        "checks": {},
    }

    result["checks"]["interface"] = check_interface(args.interface)

    try:
        import cyclonedds  # noqa: F401
        import unitree_sdk2py
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
        from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_, WirelessController_

        result["checks"]["sdk_import"] = {
            "status": "OK",
            "unitree_sdk2py": str(unitree_sdk2py.__file__),
        }
    except Exception as exc:
        result["checks"]["sdk_import"] = {"status": "FAIL", "error": f"{exc.__class__.__name__}: {exc}"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    try:
        ChannelFactoryInitialize(args.domain_id, args.interface)
        result["checks"]["dds_init"] = {"status": "OK"}
    except Exception as exc:
        result["checks"]["dds_init"] = {"status": "FAIL", "error": f"{exc.__class__.__name__}: {exc}"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 3

    high_state = read_samples(
        ChannelSubscriber,
        HIGH_STATE_TOPIC,
        SportModeState_,
        args.samples,
        args.timeout_sec,
        summarize_high_state,
    )
    result["checks"]["high_state"] = high_state

    wireless = read_samples(
        ChannelSubscriber,
        WIRELESS_TOPIC,
        WirelessController_,
        args.samples,
        args.timeout_sec,
        summarize_wireless,
    )
    result["checks"]["wireless_controller"] = wireless

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if high_state.get("status") == "OK" else 4


def check_interface(interface: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["ip", "-br", "addr", "show", "dev", interface],
            check=False,
            text=True,
            capture_output=True,
        )
    except Exception as exc:
        return {"status": "WARN", "error": f"{exc.__class__.__name__}: {exc}"}
    output = completed.stdout.strip()
    if completed.returncode != 0:
        return {"status": "FAIL", "error": completed.stderr.strip() or output}
    return {"status": "OK" if output else "FAIL", "output": output}


def read_samples(
    subscriber_cls: Any,
    topic: str,
    data_type: Any,
    sample_count: int,
    timeout_sec: float,
    summarizer: Any,
) -> dict[str, Any]:
    subscriber = None
    samples: list[dict[str, Any]] = []
    started = time.monotonic()
    try:
        subscriber = subscriber_cls(topic, data_type)
        subscriber.Init()
        for _ in range(max(1, sample_count)):
            sample = subscriber.Read(timeout=timeout_sec)
            if sample is not None:
                samples.append(summarizer(sample))
        elapsed = round(time.monotonic() - started, 3)
        return {
            "status": "OK" if samples else "FAIL",
            "topic": topic,
            "samples_read": len(samples),
            "elapsed_sec": elapsed,
            "samples": samples[:3],
            "note": "subscriber read only; no publisher or motion client was created",
        }
    except Exception as exc:
        return {
            "status": "FAIL",
            "topic": topic,
            "samples_read": len(samples),
            "error": f"{exc.__class__.__name__}: {exc}",
        }
    finally:
        if subscriber is not None:
            try:
                subscriber.Close()
            except Exception:
                pass


def summarize_high_state(sample: Any) -> dict[str, Any]:
    return {
        "mode": safe_value(getattr(sample, "mode", None)),
        "gait_type": safe_value(getattr(sample, "gait_type", None)),
        "progress": safe_value(getattr(sample, "progress", None)),
        "position": safe_value(getattr(sample, "position", None)),
        "velocity": safe_value(getattr(sample, "velocity", None)),
        "yaw_speed": safe_value(getattr(sample, "yaw_speed", None)),
        "body_height": safe_value(getattr(sample, "body_height", None)),
        "error_code": safe_value(getattr(sample, "error_code", None)),
    }


def summarize_wireless(sample: Any) -> dict[str, Any]:
    return {
        "lx": safe_value(getattr(sample, "lx", None)),
        "ly": safe_value(getattr(sample, "ly", None)),
        "rx": safe_value(getattr(sample, "rx", None)),
        "ry": safe_value(getattr(sample, "ry", None)),
        "keys": safe_value(getattr(sample, "keys", None)),
    }


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


if __name__ == "__main__":
    raise SystemExit(main())
