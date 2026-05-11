# Go2 C++ SportClient Scan

- Source: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2/include/unitree/robot/go2/sport/sport_client.hpp`
- API constants: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2/include/unitree/robot/go2/sport/sport_api.hpp`
- unitree_sdk2 commit: `6d03531e109135b18500c7c3e6f8408ba857134e`
- Methods found: 39

| API ID | Official Name | C++ Method | Parameters | Conservative Risk |
| --- | --- | --- | --- | --- |
| 1001 | Damp | Damp |  | disabled |
| 1002 | BalanceStand | BalanceStand |  | safe |
| 1003 | StopMove | StopMove |  | safe |
| 1004 | StandUp | StandUp |  | safe |
| 1005 | StandDown | StandDown |  | safe |
| 1006 | RecoveryStand | RecoveryStand |  | safe |
| 1007 | Euler | Euler | roll, pitch, yaw | caution |
| 1008 | Move | Move | vx, vy, vyaw | safe |
| 1009 | Sit | Sit |  | safe |
| 1010 | RiseSit | RiseSit |  | safe |
| 1015 | SpeedLevel | SpeedLevel | level | caution |
| 1016 | Hello | Hello |  | safe |
| 1017 | Stretch | Stretch |  | safe |
| 1020 | Content | Content |  | safe |
| 1022 | Dance1 | Dance1 |  | caution |
| 1023 | Dance2 | Dance2 |  | caution |
| 1027 | SwitchJoystick | SwitchJoystick | flag | disabled |
| 1028 | Pose | Pose | flag | caution |
| 1029 | Scrape | Scrape |  | dangerous |
| 1030 | FrontFlip | FrontFlip |  | dangerous |
| 1031 | FrontJump | FrontJump |  | dangerous |
| 1032 | FrontPounce | FrontPounce |  | dangerous |
| 1036 | Heart | Heart |  | safe |
| 1061 | StaticWalk | StaticWalk |  | safe |
| 1062 | TrotRun | TrotRun |  | dangerous |
| 1063 | EconomicGait | EconomicGait |  | caution |
| 2041 | LeftFlip | LeftFlip |  | dangerous |
| 2043 | BackFlip | BackFlip |  | dangerous |
| 2044 | HandStand | HandStand | flag | dangerous |
| 2045 | FreeWalk | FreeWalk |  | caution |
| 2046 | FreeBound | FreeBound | flag | dangerous |
| 2047 | FreeJump | FreeJump | flag | dangerous |
| 2048 | FreeAvoid | FreeAvoid | flag | safe |
| 2049 | ClassicWalk | ClassicWalk | flag | caution |
| 2050 | WalkUpright | WalkUpright | flag | caution |
| 2051 | CrossStep | CrossStep | flag | caution |
| 2054 | AutoRecoverSet | AutoRecoverSet | flag | caution |
| 2055 | AutoRecoverGet | AutoRecoverGet | flag | caution |
| 2058 | SwitchAvoidMode | SwitchAvoidMode |  | safe |

## Python/C++ Differences

| API ID | Python Method | C++ Method | Meaning |
| --- | --- | --- | --- |
| 1063 | (registered only) | EconomicGait | Python wrapper missing |
| 2054 | AutoRecoverySet | AutoRecoverSet | same API ID, language naming differs |
| 2055 | AutoRecoveryGet | AutoRecoverGet | same API ID, language naming differs |

## SDK Coverage Notes

- C++ APIs not represented by Python API ID: none
- Python APIs not represented by C++ API ID: none
- `TrajectoryFollow` appears in a C++ example file but is not declared in the currently scanned Go2 C++ SportClient header and is not exposed by the Python Go2 SportClient.
- This scan read local files only and did not call any SDK method.
