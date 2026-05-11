# Go2 Python SportClient Scan

- Source: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2_python/unitree_sdk2py/go2/sport/sport_client.py`
- API constants: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2_python/unitree_sdk2py/go2/sport/sport_api.py`
- unitree_sdk2_python commit: `d9467c5fbe5428442048d4ebd2dec4b8f719a7c8`
- Actions found: 39

| API ID | Official Name | Python Method | Parameters | Registered | Method Present | Conservative Risk |
| --- | --- | --- | --- | --- | --- | --- |
| 1001 | Damp | Damp |  | yes | yes | disabled |
| 1002 | BalanceStand | BalanceStand |  | yes | yes | safe |
| 1003 | StopMove | StopMove |  | yes | yes | safe |
| 1004 | StandUp | StandUp |  | yes | yes | safe |
| 1005 | StandDown | StandDown |  | yes | yes | safe |
| 1006 | RecoveryStand | RecoveryStand |  | yes | yes | safe |
| 1007 | Euler | Euler | roll, pitch, yaw | yes | yes | caution |
| 1008 | Move | Move | vx, vy, vyaw | yes | yes | safe |
| 1009 | Sit | Sit |  | yes | yes | safe |
| 1010 | RiseSit | RiseSit |  | yes | yes | safe |
| 1015 | SpeedLevel | SpeedLevel | level | yes | yes | caution |
| 1016 | Hello | Hello |  | yes | yes | safe |
| 1017 | Stretch | Stretch |  | yes | yes | safe |
| 1020 | Content | Content |  | yes | yes | safe |
| 1022 | Dance1 | Dance1 |  | yes | yes | caution |
| 1023 | Dance2 | Dance2 |  | yes | yes | caution |
| 1027 | SwitchJoystick | SwitchJoystick | on | yes | yes | disabled |
| 1028 | Pose | Pose | flag | yes | yes | caution |
| 1029 | Scrape | Scrape |  | yes | yes | dangerous |
| 1030 | FrontFlip | FrontFlip |  | yes | yes | dangerous |
| 1031 | FrontJump | FrontJump |  | yes | yes | dangerous |
| 1032 | FrontPounce | FrontPounce |  | yes | yes | dangerous |
| 1036 | Heart | Heart |  | yes | yes | safe |
| 1061 | StaticWalk | StaticWalk |  | yes | yes | safe |
| 1062 | TrotRun | TrotRun |  | yes | yes | dangerous |
| 1063 | EconomicGait |  |  | yes | no | caution |
| 2041 | LeftFlip | LeftFlip |  | yes | yes | dangerous |
| 2043 | BackFlip | BackFlip |  | yes | yes | dangerous |
| 2044 | HandStand | HandStand | flag | yes | yes | dangerous |
| 2045 | FreeWalk | FreeWalk |  | yes | yes | caution |
| 2046 | FreeBound | FreeBound | flag | yes | yes | dangerous |
| 2047 | FreeJump | FreeJump | flag | yes | yes | dangerous |
| 2048 | FreeAvoid | FreeAvoid | flag | yes | yes | safe |
| 2049 | ClassicWalk | ClassicWalk | flag | yes | yes | caution |
| 2050 | WalkUpright | WalkUpright | flag | yes | yes | caution |
| 2051 | CrossStep | CrossStep | flag | yes | yes | caution |
| 2054 | AutoRecoverySet | AutoRecoverySet | enabled | yes | yes | caution |
| 2055 | AutoRecoveryGet | AutoRecoveryGet |  | yes | yes | caution |
| 2058 | SwitchAvoidMode | SwitchAvoidMode |  | yes | yes | safe |

## Notes

- `EconomicGait` is registered with API ID 1063 but has no Python wrapper method in the scanned file.
- `Move` uses `_CallNoReply`; project voice control wraps it with bounded speed/duration and then calls `StopMove`.
- This scan read local files only and did not call any SDK method.
