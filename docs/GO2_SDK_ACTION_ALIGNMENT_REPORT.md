# Go2 SDK Action Alignment Report

## 1. SDK source

- unitree_sdk2_python path: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2_python`
- commit: `d9467c5fbe5428442048d4ebd2dec4b8f719a7c8`
- scanned file: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2_python/unitree_sdk2py/go2/sport/sport_client.py`
- scanned API registry: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2_python/unitree_sdk2py/go2/sport/sport_api.py`
- generated catalog: `configs/go2_action_catalog.generated.yaml`
- project catalog: `configs/go2_action_catalog.yaml`

## 2. Actions found in SDK

The local SDK scan found 39 Go2 SportClient entries.

| API ID | Official Name | SDK Method | Parameters | Method Present |
| --- | --- | --- | --- | --- |
| 1001 | Damp | Damp |  | yes |
| 1002 | BalanceStand | BalanceStand |  | yes |
| 1003 | StopMove | StopMove |  | yes |
| 1004 | StandUp | StandUp |  | yes |
| 1005 | StandDown | StandDown |  | yes |
| 1006 | RecoveryStand | RecoveryStand |  | yes |
| 1007 | Euler | Euler | roll, pitch, yaw | yes |
| 1008 | Move | Move | vx, vy, vyaw | yes |
| 1009 | Sit | Sit |  | yes |
| 1010 | RiseSit | RiseSit |  | yes |
| 1015 | SpeedLevel | SpeedLevel | level | yes |
| 1016 | Hello | Hello |  | yes |
| 1017 | Stretch | Stretch |  | yes |
| 1020 | Content | Content |  | yes |
| 1022 | Dance1 | Dance1 |  | yes |
| 1023 | Dance2 | Dance2 |  | yes |
| 1027 | SwitchJoystick | SwitchJoystick | on | yes |
| 1028 | Pose | Pose | flag | yes |
| 1029 | Scrape | Scrape |  | yes |
| 1030 | FrontFlip | FrontFlip |  | yes |
| 1031 | FrontJump | FrontJump |  | yes |
| 1032 | FrontPounce | FrontPounce |  | yes |
| 1036 | Heart | Heart |  | yes |
| 1061 | StaticWalk | StaticWalk |  | yes |
| 1062 | TrotRun | TrotRun |  | yes |
| 1063 | EconomicGait |  |  | no |
| 2041 | LeftFlip | LeftFlip |  | yes |
| 2043 | BackFlip | BackFlip |  | yes |
| 2044 | HandStand | HandStand | flag | yes |
| 2045 | FreeWalk | FreeWalk |  | yes |
| 2046 | FreeBound | FreeBound | flag | yes |
| 2047 | FreeJump | FreeJump | flag | yes |
| 2048 | FreeAvoid | FreeAvoid | flag | yes |
| 2049 | ClassicWalk | ClassicWalk | flag | yes |
| 2050 | WalkUpright | WalkUpright | flag | yes |
| 2051 | CrossStep | CrossStep | flag | yes |
| 2054 | AutoRecoverySet | AutoRecoverySet | enabled | yes |
| 2055 | AutoRecoveryGet | AutoRecoveryGet |  | yes |
| 2058 | SwitchAvoidMode | SwitchAvoidMode |  | yes |

## 3. Actions already in project catalog

All 39 scanned SDK API entries are represented in the project catalog by either the same intent name or the same official API.

- Exact or direct catalog entries: `damp`, `balance_stand`, `stand_up`, `stand_down`, `recovery_stand`, `euler`, `move`, `rise_sit`, `speed_level`, `hello`, `stretch`, `content`, `dance1`, `dance2`, `switch_joystick`, `pose`, `scrape`, `front_flip`, `front_jump`, `front_pounce`, `heart`, `static_walk`, `trot_run`, `economic_gait`, `left_flip`, `back_flip`, `hand_stand`, `free_walk`, `free_bound`, `free_jump`, `free_avoid`, `classic_walk`, `walk_upright`, `cross_step`, `auto_recovery_set`, `auto_recovery_get`, `switch_avoid_mode`
- Project intent `stop` maps to official SDK action `StopMove` / API `1003`.
- Project intent `sit_down` maps to official SDK action `Sit` / API `1009`.
- Project intents `move_forward`, `move_backward`, `turn_left`, and `turn_right` are bounded voice wrappers over official SDK action `Move` / API `1008`.

## 4. Actions missing from project catalog

None by official API ID or official action name.

Naming differences that should stay documented:

- SDK generated intent `stop_move` is represented by project intent `stop`.
- SDK generated intent `sit` is represented by project intent `sit_down`.
- SDK action `Move` is additionally represented by bounded project intents `move_forward`, `move_backward`, `turn_left`, and `turn_right`.

## 5. Actions in project catalog but not found in SDK

These entries are project-specific wrappers, read-only/status concepts, or disabled scope markers rather than direct SportClient methods found by the scanner.

| Project Intent | Project Official Name | Status |
| --- | --- | --- |
| `move_forward` | Move | bounded wrapper over `Move(vx, vy, vyaw)` |
| `move_backward` | Move | bounded wrapper over `Move(vx, vy, vyaw)` |
| `turn_left` | Move | bounded wrapper over `Move(vx, vy, vyaw)` |
| `turn_right` | Move | bounded wrapper over `Move(vx, vy, vyaw)` |
| `status_report` | SportModeState | read-only project status action, not a scanned SportClient method |
| `trajectory_follow` | TrajectoryFollow | disabled placeholder, not found in current SportClient scan |
| `low_level_motor_control` | Low-level motor control | explicitly out of project scope |

## 6. Risk level comparison

The generated SDK catalog marks every scanned action as `disabled`, `voice_enabled: false`, and `real_robot_enabled: false` because it is scan output only.

The curated project catalog keeps the actual safety policy:

- Safe voice/mock actions include posture, status, and bounded movement commands.
- Raw `Move(vx, vy, vyaw)` remains disabled for direct voice use.
- Caution actions such as dances, pose, gait/mode changes, and speed/attitude controls remain either real-robot disabled or voice disabled.
- Dangerous actions remain real-robot disabled and voice disabled: `front_flip`, `back_flip`, `left_flip`, `front_jump`, `front_pounce`, `hand_stand`, `free_bound`, `free_jump`, `trot_run`, `scrape`, `walk_upright`, `cross_step`.
- Global runtime configuration is still `robot_mode: mock` and `enable_real_robot: false`; no real robot command was sent during this scan or alignment.

## 7. Recommended catalog updates

- Keep `configs/go2_action_catalog.yaml` as the only runtime action catalog.
- Do not copy generated actions directly into the runtime catalog without safety review.
- Keep `stop` and `sit_down` as user-facing project intent names, with the official SDK mapping documented.
- Keep bounded wrappers for `Move`; do not expose raw `Move(vx, vy, vyaw)` to voice.
- Keep `EconomicGait` disabled because the API is registered but no local `SportClient` wrapper method was found.
- Keep `TrajectoryFollow` disabled until a validated path-input workflow exists.

## 8. Actions still disabled for real robot

- Direct/raw control: `move`, `speed_level`, `euler`, `switch_joystick`, `auto_recovery_set`, `damp`, `trajectory_follow`, `economic_gait`, `low_level_motor_control`
- Caution preset/mode actions disabled for real robot: `dance1`, `dance2`, `pose`, `free_walk`, `classic_walk`
- Dangerous actions disabled for real robot: `front_flip`, `back_flip`, `left_flip`, `front_jump`, `front_pounce`, `hand_stand`, `free_bound`, `free_jump`, `trot_run`, `scrape`, `walk_upright`, `cross_step`

## 9. Notes

- This report is based on the local SDK source checked out under `third_party/`, not on a web-only action table.
- `unitree_sdk2py` import and `SportClient` import both passed in the project `.venv`.
- CycloneDDS Python `0.10.2` needed a local CycloneDDS C library and Python 3.14 compatibility patches inside the project `.venv`.
- No ROS2 workspace was built and no ROS2 launch file was run.
- No Go2 motion command was sent.
