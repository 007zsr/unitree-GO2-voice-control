# Go2 Disabled and Dangerous Commands

These commands must remain unavailable for voice-triggered real-robot execution.

| Command | Disabled reason | SDK exists | Project recognizes | Mock simulation | Real robot allowed |
| --- | --- | --- | --- | --- | --- |
| FrontFlip | flip can cause falls, collisions, or hardware damage | yes | yes | yes | false |
| BackFlip | flip can cause falls, collisions, or hardware damage | yes | yes | yes | false |
| LeftFlip | flip can cause falls, collisions, or hardware damage | yes | yes | yes | false |
| FrontJump | jump can cause collision or loss of balance | yes | yes | yes | false |
| FrontPounce | pounce can cause collision or loss of balance | yes | yes | yes | false |
| HandStand | inverted posture requires special supervision | yes | yes | yes | false |
| FreeBound | bounding gait has high movement uncertainty | yes | yes | yes | false |
| FreeJump | jump mode has high movement uncertainty | yes | yes | yes | false |
| TrotRun | high-speed running is not a voice-safe first test | yes | yes | yes | false |
| Scrape | behavior is not confirmed enough for voice real-robot execution | yes | yes | yes | false |
| SwitchJoystick | control authority switch must not be voice-triggered | yes | yes | yes | false |
| SpeedLevel | speed level changes can raise motion risk; high-speed settings remain disabled | yes | yes | yes | false |
| low_level_motor_control | official low-level control can conflict with high-level sport service | no | yes | no | false |
| TrajectoryFollow | requires validated path input and is not exposed by scanned Python/header interface | no | yes | yes | false |

## Policy

- Recognition by NLU is allowed for rejection/confirmation logs, not for execution.
- Mock simulation does not imply real robot safety.
- Low-level motor control is outside this project stage.
- `TrajectoryFollow` remains disabled until path validation and current SDK method exposure are resolved.
