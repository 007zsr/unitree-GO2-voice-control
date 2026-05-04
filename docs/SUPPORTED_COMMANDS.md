# Supported Commands

The executable command whitelist is loaded from `configs/commands.yaml`.
Natural-language aliases below are used by the current rule-based NLU and GUI help.

## stop

- Display name: stop
- 中文：停 / 停下 / 停止 / 别动
- English: stop / halt / freeze
- Requires duration: no
- Requires robot standing: no
- Interruptible: yes

## stand_up

- Display name: stand up
- 中文：站起来 / 起立
- English: stand up / get up
- Requires duration: no
- Requires robot standing: no
- Interruptible: yes

## sit_down

- Display name: sit down
- 中文：坐下 / 趴下
- English: sit down / lie down
- Requires duration: no
- Requires robot standing: no
- Interruptible: yes

## move_forward

- Display name: move forward slowly
- 中文：向前走 / 前进 / 往前走
- English: move forward / go forward / walk forward
- Requires duration: yes
- Default duration: 1.0s
- Max duration: 2.0s
- Requires robot standing: yes
- Interruptible: yes

## move_backward

- Display name: move backward slowly
- 中文：后退 / 往后退 / 退后
- English: move back / move backward / go backward
- Requires duration: yes
- Default duration: 0.7s
- Max duration: 2.0s
- Requires robot standing: yes
- Interruptible: yes

## turn_left

- Display name: turn left slowly
- 中文：左转 / 向左转
- English: turn left / left
- Requires duration: yes
- Default duration: 0.7s
- Max duration: 1.0s
- Requires robot standing: yes
- Interruptible: yes

## turn_right

- Display name: turn right slowly
- 中文：右转 / 向右转
- English: turn right / right
- Requires duration: yes
- Default duration: 0.7s
- Max duration: 1.0s
- Requires robot standing: yes
- Interruptible: yes

## status_report

- Display name: report status
- 中文：报告状态 / 状态 / 电量
- English: report status / status / battery
- Requires duration: no
- Requires robot standing: no
- Interruptible: yes

## Notes

- Default robot mode remains Mock.
- `stop` is always highest priority and is not blocked by normal duplicate-command filtering.
- Strict command mode prefers clear commands such as `Go2, sit down`, `Please stand up`, `机器狗，坐下`, or short direct commands.
