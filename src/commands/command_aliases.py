from __future__ import annotations


COMMAND_ALIASES: dict[str, dict[str, list[str]]] = {
    "stop": {
        "zh": ["停", "停下", "停止", "别动"],
        "en": ["stop", "halt", "freeze"],
    },
    "stand_up": {
        "zh": ["站起来", "起立"],
        "en": ["stand up", "get up"],
    },
    "sit_down": {
        "zh": ["坐下", "趴下"],
        "en": ["sit down", "lie down"],
    },
    "move_forward": {
        "zh": ["向前走", "前进", "往前走"],
        "en": ["move forward", "go forward", "walk forward"],
    },
    "move_backward": {
        "zh": ["后退", "往后退", "退后"],
        "en": ["move back", "move backward", "go backward"],
    },
    "turn_left": {
        "zh": ["左转", "向左转"],
        "en": ["turn left", "left"],
    },
    "turn_right": {
        "zh": ["右转", "向右转"],
        "en": ["turn right", "right"],
    },
    "status_report": {
        "zh": ["报告状态", "状态", "电量"],
        "en": ["report status", "status", "battery"],
    },
}


def aliases_for_intent(intent: str) -> dict[str, list[str]]:
    return COMMAND_ALIASES.get(intent, {"zh": [], "en": []})
