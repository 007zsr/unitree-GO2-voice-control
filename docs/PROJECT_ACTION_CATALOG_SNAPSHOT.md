# Project Action Catalog Snapshot

- Source: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/configs/go2_action_catalog.yaml`
- Actions: 46
- This snapshot is the runtime command truth for aliases, risk, mock availability, and real-robot availability.

| Intent | Official | SDK Method | API ID | Risk | Voice | Mock | Real | Standing | Confirm | Aliases EN | Aliases ZH |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stop | StopMove | StopMove | 1003 | safe | True | True | True | False | False | stop, stop moving, halt, freeze, emergency stop, do not move, don't move, hold still, stay still, stay there, stand still | 停止, 停下, 别动, 立刻停止, 急停, 不要动, 原地待命, 原地别动, 保持不动, 停在原地, 别移动 |
| balance_stand | BalanceStand | BalanceStand | 1002 | safe | True | True | True | False | False | balance stand, balanced stand | 平衡站立, 保持站立 |
| stand_up | StandUp | StandUp | 1004 | safe | True | True | True | False | False | stand up, get up, rise | 站起来, 起立, 站起 |
| stand_down | StandDown | StandDown | 1005 | safe | True | True | True | False | False | stand down, lie down | 趴下, 卧倒 |
| recovery_stand | RecoveryStand | RecoveryStand | 1006 | safe | True | True | True | False | False | recovery stand, recover stand, recover standing | 恢复站立, 恢复起立 |
| sit_down | Sit | Sit | 1009 | safe | True | True | True | False | False | sit, sit down | 坐下, 坐好 |
| rise_sit | RiseSit | RiseSit | 1010 | safe | True | True | True | False | False | rise sit, stand from sit | 从坐姿站起, 坐姿起立 |
| move | Move | Move | 1008 | disabled | False | True | False | True | False | generic move | 通用移动 |
| move_forward | Move | Move | 1008 | safe | True | True | True | True | False | move forward, go forward, walk forward, forward | 向前走, 前进, 往前走 |
| move_backward | Move | Move | 1008 | safe | True | True | True | True | False | move back, move backward, go backward, backward | 后退, 往后退, 向后退 |
| turn_left | Move | Move | 1008 | safe | True | True | True | True | False | turn left, left | 左转, 向左转 |
| turn_right | Move | Move | 1008 | safe | True | True | True | True | False | turn right, right | 右转, 向右转 |
| status_report | SportModeState |  |  | safe | True | True | True | False | False | report status, status, battery | 报告状态, 状态, 电量 |
| speed_level | SpeedLevel | SpeedLevel | 1015 | caution | False | True | False | False | False | speed level, change speed | 速度等级, 调整速度 |
| euler | Euler | Euler | 1007 | caution | False | True | False | False | False | euler, change attitude, adjust attitude | 姿态调整, 欧拉角 |
| hello | Hello | Hello | 1016 | safe | True | True | True | False | False | hello, say hello, wave | 打招呼, 招手, 你好 |
| stretch | Stretch | Stretch | 1017 | safe | True | True | True | False | False | stretch, stretch body | 伸展, 伸个懒腰 |
| content | Content | Content | 1020 | safe | False | True | True | False | False | content motion | 开心动作 |
| heart | Heart | Heart | 1036 | safe | True | True | True | False | False | heart, make a heart | 比心, 爱心 |
| static_walk | StaticWalk | StaticWalk | 1061 | safe | True | True | True | False | False | static walk | 静态步态, 静态走 |
| free_avoid | FreeAvoid | FreeAvoid | 2048 | safe | False | True | True | False | False | free avoid, enable free avoid | 开启避障, 自由避障 |
| switch_avoid_mode | SwitchAvoidMode | SwitchAvoidMode | 2058 | safe | False | True | True | False | False | switch avoid mode, toggle avoid mode | 切换避障模式, 切换避障 |
| auto_recovery_get | AutoRecoveryGet | AutoRecoveryGet | 2055 | safe | False | True | True | False | False | get auto recovery, auto recovery status | 查询自动恢复, 自动恢复状态 |
| dance1 | Dance1 | Dance1 | 1022 | caution | True | True | False | False | False | dance, dance one, dance 1 | 跳舞, 舞蹈一, 跳第一个舞 |
| dance2 | Dance2 | Dance2 | 1023 | caution | True | True | False | False | False | dance two, dance 2, second dance | 舞蹈二, 跳第二个舞 |
| pose | Pose | Pose | 1028 | caution | True | True | False | False | False | pose, strike a pose | 摆姿势, 姿势 |
| free_walk | FreeWalk | FreeWalk | 2045 | caution | True | True | False | False | False | free walk | 自由走, 自由步态 |
| classic_walk | ClassicWalk | ClassicWalk | 2049 | caution | True | True | False | False | False | classic walk | 经典步态, 经典走 |
| auto_recovery_set | AutoRecoverySet | AutoRecoverySet | 2054 | caution | False | True | False | False | False | set auto recovery, enable auto recovery | 设置自动恢复, 开启自动恢复 |
| damp | Damp | Damp | 1001 | disabled | False | True | False | False | False | damp | 阻尼 |
| trajectory_follow | TrajectoryFollow | TrajectoryFollow |  | disabled | False | True | False | False | False | trajectory follow, follow trajectory | 轨迹跟踪, 跟随轨迹 |
| switch_joystick | SwitchJoystick | SwitchJoystick | 1027 | disabled | False | True | False | False | False | switch joystick, toggle joystick | 切换手柄, 切换摇杆 |
| economic_gait | EconomicGait | EconomicGait | 1063 | disabled | False | True | False | False | False | economic gait | 经济步态 |
| low_level_motor_control | Low-level motor control |  |  | disabled | False | False | False | False | False | low level control, motor control | 低层控制, 电机控制 |
| front_flip | FrontFlip | FrontFlip | 1030 | dangerous | False | True | False | False | True | front flip, flip forward, forward flip | 前空翻, 向前翻, 前翻 |
| back_flip | BackFlip | BackFlip | 2043 | dangerous | False | True | False | False | True | back flip, backflip, flip backward | 后空翻, 向后翻, 后翻 |
| left_flip | LeftFlip | LeftFlip | 2041 | dangerous | False | True | False | False | True | left flip, flip left | 左翻, 向左翻 |
| front_jump | FrontJump | FrontJump | 1031 | dangerous | False | True | False | False | True | jump, front jump, jump forward | 跳, 跳跃, 向前跳 |
| front_pounce | FrontPounce | FrontPounce | 1032 | dangerous | False | True | False | False | True | pounce, front pounce, pounce forward | 扑, 扑击, 向前扑 |
| hand_stand | HandStand | HandStand | 2044 | dangerous | False | True | False | False | True | handstand, hand stand | 倒立 |
| free_bound | FreeBound | FreeBound | 2046 | dangerous | False | True | False | False | True | free bound, bound | 自由跳跃步态, 弹跳步态 |
| free_jump | FreeJump | FreeJump | 2047 | dangerous | False | True | False | False | True | free jump | 自由跳 |
| trot_run | TrotRun | TrotRun | 1062 | dangerous | False | True | False | False | True | trot run, run fast, sprint | 快跑, 高速跑, 小跑 |
| scrape | Scrape | Scrape | 1029 | dangerous | False | True | False | False | True | scrape | 刮擦, scrape |
| walk_upright | WalkUpright | WalkUpright | 2050 | dangerous | False | True | False | False | True | walk upright, upright walk | 直立行走, 直立走 |
| cross_step | CrossStep | CrossStep | 2051 | dangerous | False | True | False | False | True | cross step | 交叉步 |
