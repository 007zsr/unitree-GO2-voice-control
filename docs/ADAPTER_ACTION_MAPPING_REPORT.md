# Adapter Action Mapping Report

- MockAdapter: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/src/robot/mock_adapter.py`
- Go2Adapter: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/src/robot/go2_adapter.py`

| Intent | Mock | Mock Mapping | Go2Adapter | Go2 SDK Call | Go2 Mapping | Needs Params | May Move | Real Default |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stop | yes | explicit MockAdapter branch | yes | StopMove | explicit Go2Adapter stop branch | no | stop request | True |
| balance_stand | yes | explicit MockAdapter branch | yes | BalanceStand | generic catalog action branch | no | yes | True |
| stand_up | yes | explicit MockAdapter branch | yes | StandUp | explicit Go2Adapter branch | no | yes | True |
| stand_down | yes | explicit MockAdapter branch | yes | StandDown | generic catalog action branch | no | yes | True |
| recovery_stand | yes | explicit MockAdapter branch | yes | RecoveryStand | generic catalog action branch | no | yes | True |
| sit_down | yes | explicit MockAdapter branch | yes | Sit/StandDown fallback | explicit Go2Adapter branch | no | yes | True |
| rise_sit | yes | explicit MockAdapter branch | yes | RiseSit | generic catalog action branch | no | yes | True |
| move | yes | generic catalog simulation | no | Move | Go2Adapter rejects real_robot_enabled=false | no | yes | False |
| move_forward | yes | explicit MockAdapter branch | yes | Move + StopMove | bounded velocity branch | yes | yes | True |
| move_backward | yes | explicit MockAdapter branch | yes | Move + StopMove | bounded velocity branch | yes | yes | True |
| turn_left | yes | explicit MockAdapter branch | yes | Move + StopMove | bounded velocity branch | yes | yes | True |
| turn_right | yes | explicit MockAdapter branch | yes | Move + StopMove | bounded velocity branch | yes | yes | True |
| status_report | yes | explicit MockAdapter branch | yes | state subscriber | read-only Go2Adapter branch | no | read/status | True |
| speed_level | yes | generic catalog simulation | no | SpeedLevel | Go2Adapter rejects real_robot_enabled=false | yes | yes or high uncertainty | False |
| euler | yes | generic catalog simulation | no | Euler | Go2Adapter rejects real_robot_enabled=false | yes | yes or high uncertainty | False |
| hello | yes | generic catalog simulation | yes | Hello | generic catalog action branch | no | yes | True |
| stretch | yes | generic catalog simulation | yes | Stretch | generic catalog action branch | no | yes | True |
| content | yes | generic catalog simulation | yes | Content | generic catalog action branch | no | yes | True |
| heart | yes | generic catalog simulation | yes | Heart | generic catalog action branch | no | yes | True |
| static_walk | yes | generic catalog simulation | yes | StaticWalk | generic catalog action branch | no | yes | True |
| free_avoid | yes | generic catalog simulation | yes | FreeAvoid | generic catalog action branch | yes | mode switch | True |
| switch_avoid_mode | yes | generic catalog simulation | yes | SwitchAvoidMode | generic catalog action branch | no | mode switch | True |
| auto_recovery_get | yes | generic catalog simulation | yes | AutoRecoveryGet | generic catalog action branch | no | read/status | True |
| dance1 | yes | generic catalog simulation | no | Dance1 | Go2Adapter rejects real_robot_enabled=false | no | yes or high uncertainty | False |
| dance2 | yes | generic catalog simulation | no | Dance2 | Go2Adapter rejects real_robot_enabled=false | no | yes or high uncertainty | False |
| pose | yes | generic catalog simulation | no | Pose | Go2Adapter rejects real_robot_enabled=false | yes | yes or high uncertainty | False |
| free_walk | yes | generic catalog simulation | no | FreeWalk | Go2Adapter rejects real_robot_enabled=false | no | yes or high uncertainty | False |
| classic_walk | yes | generic catalog simulation | no | ClassicWalk | Go2Adapter rejects real_robot_enabled=false | yes | yes or high uncertainty | False |
| auto_recovery_set | yes | generic catalog simulation | no | AutoRecoverySet | Go2Adapter rejects real_robot_enabled=false | yes | yes or high uncertainty | False |
| damp | yes | generic catalog simulation | no | Damp | Go2Adapter rejects real_robot_enabled=false | no | unknown | False |
| trajectory_follow | yes | generic catalog simulation | no | TrajectoryFollow | Go2Adapter rejects real_robot_enabled=false | no | unknown | False |
| switch_joystick | yes | generic catalog simulation | no | SwitchJoystick | Go2Adapter rejects real_robot_enabled=false | yes | unknown | False |
| economic_gait | yes | generic catalog simulation | no | EconomicGait | Go2Adapter rejects real_robot_enabled=false | no | unknown | False |
| low_level_motor_control | no | mock_enabled=false | no |  | no sdk_method | no | unknown | False |
| front_flip | yes | generic catalog simulation | no | FrontFlip | Go2Adapter rejects dangerous catalog action | no | yes or high uncertainty | False |
| back_flip | yes | generic catalog simulation | no | BackFlip | Go2Adapter rejects dangerous catalog action | no | yes or high uncertainty | False |
| left_flip | yes | generic catalog simulation | no | LeftFlip | Go2Adapter rejects dangerous catalog action | no | yes or high uncertainty | False |
| front_jump | yes | generic catalog simulation | no | FrontJump | Go2Adapter rejects dangerous catalog action | no | yes or high uncertainty | False |
| front_pounce | yes | generic catalog simulation | no | FrontPounce | Go2Adapter rejects dangerous catalog action | no | yes or high uncertainty | False |
| hand_stand | yes | generic catalog simulation | no | HandStand | Go2Adapter rejects dangerous catalog action | yes | yes or high uncertainty | False |
| free_bound | yes | generic catalog simulation | no | FreeBound | Go2Adapter rejects dangerous catalog action | yes | yes or high uncertainty | False |
| free_jump | yes | generic catalog simulation | no | FreeJump | Go2Adapter rejects dangerous catalog action | yes | yes or high uncertainty | False |
| trot_run | yes | generic catalog simulation | no | TrotRun | Go2Adapter rejects dangerous catalog action | no | yes or high uncertainty | False |
| scrape | yes | generic catalog simulation | no | Scrape | Go2Adapter rejects dangerous catalog action | no | yes or high uncertainty | False |
| walk_upright | yes | generic catalog simulation | no | WalkUpright | Go2Adapter rejects dangerous catalog action | yes | yes or high uncertainty | False |
| cross_step | yes | generic catalog simulation | no | CrossStep | Go2Adapter rejects dangerous catalog action | yes | yes or high uncertainty | False |

## Notes

- MockAdapter has explicit branches for stop/posture/status/bounded movement and then generically simulates catalog actions when `mock_enabled` is not false.
- Go2Adapter has explicit branches for `stop`, `stand_up`, `sit_down`, `status_report`, and bounded velocity intents; other catalog actions require `real_robot_enabled=true`, a non-dangerous risk level, and a Python SDK method.
- `AutoRecoveryGet` returns `(code, data)` in Python SDK; the current generic Go2Adapter result handling would treat that tuple as a failure. Keep it out of first motion testing until adapter handling is adjusted.
