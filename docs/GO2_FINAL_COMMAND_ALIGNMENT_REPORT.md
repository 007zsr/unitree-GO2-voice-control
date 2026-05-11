# Go2 Final Command Alignment Report

## 1. Sources

- Python SDK path: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2_python/unitree_sdk2py/go2/sport/sport_client.py`
- Python SDK commit: `d9467c5fbe5428442048d4ebd2dec4b8f719a7c8`
- C++ SDK path: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2/include/unitree/robot/go2/sport/sport_client.hpp`
- C++ SDK commit: `6d03531e109135b18500c7c3e6f8408ba857134e`
- project catalog path: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/configs/go2_action_catalog.yaml`
- command config path: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/configs/commands.yaml`
- adapter files: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/src/robot/mock_adapter.py`, `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/src/robot/go2_adapter.py`

## 2. SDK actions found

- Python SDK SportClient entries: 39
- C++ SDK SportClient methods: 39
- Python SDK has `EconomicGait` registered but no callable wrapper method.
- C++ SDK names API 2054/2055 as `AutoRecoverSet/Get`; Python SDK and project catalog use `AutoRecoverySet/Get`.

## 3. Project catalog actions

- Project catalog actions: 46
- Catalog remains the runtime source of truth for risk, aliases, mock availability, and real-robot availability.

## 4. NLU-recognizable commands

- Catalog aliases make 46 catalog actions recognizable by rule/catalog NLU.
- Legacy `command_aliases.py` contains 8 core intents and is not the complete runtime catalog.
- Recognized dangerous/disabled aliases still produce confirmation/rejection behavior; recognition does not mean execution.

## 5. MockAdapter actions

- MockAdapter supports explicit core actions and generic catalog simulation for actions with `mock_enabled` not false.
- `low_level_motor_control` is not mock-enabled.

## 6. Go2Adapter actions

- Go2Adapter supports explicit core actions and generic catalog actions that pass catalog and SDK method gates.
- Go2Adapter does not override global `robot_mode=mock` / `enable_real_robot=false`; no real robot command can run in this configuration.

## 7. Full alignment table

| intent | Python SDK | C++ SDK | catalog | NLU | Mock | Go2Adapter | risk | real_robot_enabled | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stop | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| balance_stand | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| stand_up | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| stand_down | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| recovery_stand | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| sit_down | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| rise_sit | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| move | yes | yes | yes | yes | yes | no | disabled | False | disabled |
| move_forward | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| move_backward | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| turn_left | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| turn_right | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| status_report | no | no | yes | yes | yes | yes | safe | True | read_only_candidate |
| speed_level | yes | yes | yes | yes | yes | no | caution | False | mock_only_or_caution |
| euler | yes | yes | yes | yes | yes | no | caution | False | mock_only_or_caution |
| hello | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| stretch | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| content | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| heart | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| static_walk | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| free_avoid | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| switch_avoid_mode | yes | yes | yes | yes | yes | yes | safe | True | safe_real_robot_candidate_after_next_preflight |
| auto_recovery_get | yes | yes | yes | yes | yes | yes | safe | True | review_before_real_robot_adapter_fix_needed |
| dance1 | yes | yes | yes | yes | yes | no | caution | False | mock_only_or_caution |
| dance2 | yes | yes | yes | yes | yes | no | caution | False | mock_only_or_caution |
| pose | yes | yes | yes | yes | yes | no | caution | False | mock_only_or_caution |
| free_walk | yes | yes | yes | yes | yes | no | caution | False | mock_only_or_caution |
| classic_walk | yes | yes | yes | yes | yes | no | caution | False | mock_only_or_caution |
| auto_recovery_set | yes | yes | yes | yes | yes | no | caution | False | mock_only_or_caution |
| damp | yes | yes | yes | yes | yes | no | disabled | False | disabled |
| trajectory_follow | no | no | yes | yes | yes | no | disabled | False | disabled |
| switch_joystick | yes | yes | yes | yes | yes | no | disabled | False | disabled |
| economic_gait | yes | yes | yes | yes | yes | no | disabled | False | disabled |
| low_level_motor_control | no | no | yes | yes | no | no | disabled | False | disabled |
| front_flip | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |
| back_flip | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |
| left_flip | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |
| front_jump | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |
| front_pounce | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |
| hand_stand | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |
| free_bound | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |
| free_jump | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |
| trot_run | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |
| scrape | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |
| walk_upright | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |
| cross_step | yes | yes | yes | yes | yes | no | dangerous | False | dangerous_disabled |

## 8. Missing in catalog

| API ID | Official | Python Method | Reason |
| --- | --- | --- | --- |
| - | - | - | None by SDK API ID |

## 9. Missing in adapter

| Intent | Official | SDK Method | Reason |
| --- | --- | --- | --- |
| - | - | - | No safe real-robot catalog action is missing a Go2Adapter path |

## 10. Catalog-only / SDK missing

| Intent | Official | SDK Method | Risk | Reason |
| --- | --- | --- | --- | --- |
| status_report | SportModeState |  | safe | project wrapper/status/scope marker |
| trajectory_follow | TrajectoryFollow | TrajectoryFollow | disabled | project wrapper/status/scope marker |
| low_level_motor_control | Low-level motor control |  | disabled | project wrapper/status/scope marker |

## 11. Dangerous actions

front_flip, back_flip, left_flip, front_jump, front_pounce, hand_stand, free_bound, free_jump, trot_run, scrape, walk_upright, cross_step

## 12. Caution actions

speed_level, euler, dance1, dance2, pose, free_walk, classic_walk, auto_recovery_set

## 13. Safe candidates for first real-robot test

Read-only first: `status_report` / high-state reads. Low-risk motion candidates for a later task: `stop`, `balance_stand`, `stand_up`, `stand_down`, `recovery_stand`, `sit_down`, `rise_sit`, bounded `move_forward/move_backward/turn_left/turn_right`, `hello`, `stretch`.

## 14. Must not execute before further confirmation

front_flip, back_flip, left_flip, front_jump, front_pounce, hand_stand, free_bound, free_jump, trot_run, scrape, walk_upright, cross_step, move, damp, trajectory_follow, switch_joystick, economic_gait, low_level_motor_control, speed_level, euler, dance1, dance2, pose, free_walk, classic_walk, auto_recovery_set, auto_recovery_get

## 15. Recommended fixes before real robot

- Keep `robot_mode: mock` and `enable_real_robot: false` until a separate read-only connection check passes.
- Do not run official examples as tests; they include direct motion branches.
- Add explicit Go2Adapter handling for `AutoRecoveryGet` before using it as a real robot read/check action.
- Review `auto_recovery_get`: current catalog marks it `safe`, while the conservative pre-real policy should treat it as `caution` until explicit adapter handling exists.
- Keep `walk_upright` and `cross_step` at the current stricter project level (`dangerous`) even though some planning lists classify them as `caution`.
- Keep `EconomicGait` disabled because Python SDK registration exists but no Python wrapper method was scanned.
- Keep `TrajectoryFollow` disabled; the example references it, but current scanned SportClient interfaces do not expose it.
