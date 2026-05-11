# Go2 Real Robot Candidate Commands

This file prepares the next stages only. None of these commands were executed in this audit.

## 1. Read-only / Non-motion Candidates

| Candidate | Motion | Open Space | Human Support | Emergency Stop |
| --- | --- | --- | --- | --- |
| SDK import status | no | no | no | no |
| network interface check | no | no | no | no |
| high state subscription/read | no | no | no | no |
| wireless controller state read | no | no | no | no |

## 2. Low-risk Motion Candidates For Later Testing

| Candidate | Effect | May Move | Needs Open Space | Needs Standing | Emergency Stop Ready |
| --- | --- | --- | --- | --- | --- |
| StopMove | stop request | no locomotion | operator should watch | no | yes |
| BalanceStand | posture/mode | yes | yes | not necessarily | yes |
| StandUp | posture | yes | yes | no | yes |
| StandDown | posture | yes | yes | yes | yes |
| RecoveryStand | posture | yes | yes | no | yes |
| Sit | posture | yes | yes | yes | yes |
| RiseSit | posture | yes | yes | yes | yes |
| Move(vx/vy/vyaw bounded) | locomotion | yes | yes | yes | yes |
| Hello | preset motion | yes | yes | likely standing | yes |
| Stretch | preset motion | yes | yes | likely standing | yes |

## 3. Required Gates Before Any Motion

- Complete a separate read-only connection check first.
- Confirm `robot_mode=go2` and `enable_real_robot=true` only in the dedicated motion-test task.
- Use an open area, human supervision, and a physical emergency-stop plan.
- Test one command at a time, starting with read/status and StopMove behavior.
