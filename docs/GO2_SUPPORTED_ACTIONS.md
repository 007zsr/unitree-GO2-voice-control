# Go2 Supported Actions and Voice Commands

Generated from `configs/go2_action_catalog.yaml`.

Official SDK support does not mean real-robot execution is enabled. Safety remains the final gate.

## Safe

### auto_recovery_get

- Official SDK method: `AutoRecoveryGet`
- Risk level: `safe`
- English aliases: get auto recovery, auto recovery status
- Chinese aliases: 查询自动恢复, 自动恢复状态
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Read auto-recovery setting.

### balance_stand

- Official SDK method: `BalanceStand`
- Risk level: `safe`
- English aliases: balance stand, balanced stand
- Chinese aliases: 平衡站立, 保持站立
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Enter balanced standing mode.

### content

- Official SDK method: `Content`
- Risk level: `safe`
- English aliases: content motion
- Chinese aliases: 开心动作
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Meaning is not obvious enough for direct voice by default.

### free_avoid

- Official SDK method: `FreeAvoid`
- Risk level: `safe`
- English aliases: free avoid, enable free avoid
- Chinese aliases: 开启避障, 自由避障
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Mode switches are visible in GUI but not direct voice by default.

### heart

- Official SDK method: `Heart`
- Risk level: `safe`
- English aliases: heart, make a heart
- Chinese aliases: 比心, 爱心
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Play the heart preset motion.

### hello

- Official SDK method: `Hello`
- Risk level: `safe`
- English aliases: hello, say hello, wave
- Chinese aliases: 打招呼, 招手, 你好
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Play the hello motion.

### move_backward

- Official SDK method: `Move`
- Risk level: `safe`
- English aliases: move back, move backward, go backward, backward
- Chinese aliases: 后退, 往后退, 向后退
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `True`
- Reason: Move backward slowly for a bounded duration.

### move_forward

- Official SDK method: `Move`
- Risk level: `safe`
- English aliases: move forward, go forward, walk forward, forward
- Chinese aliases: 向前走, 前进, 往前走
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `True`
- Reason: Move is only exposed through low-speed bounded commands.

### recovery_stand

- Official SDK method: `RecoveryStand`
- Risk level: `safe`
- English aliases: recovery stand, recover stand, recover standing
- Chinese aliases: 恢复站立, 恢复起立
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Recovery can help restore posture but still needs operator supervision on a real robot.

### rise_sit

- Official SDK method: `RiseSit`
- Risk level: `safe`
- English aliases: rise sit, stand from sit
- Chinese aliases: 从坐姿站起, 坐姿起立
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Rise from sitting posture.

### sit_down

- Official SDK method: `Sit`
- Risk level: `safe`
- English aliases: sit, sit down
- Chinese aliases: 坐下, 坐好
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Sit down.

### stand_down

- Official SDK method: `StandDown`
- Risk level: `safe`
- English aliases: stand down, lie down
- Chinese aliases: 趴下, 卧倒
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Stand down or lie down.

### stand_up

- Official SDK method: `StandUp`
- Risk level: `safe`
- English aliases: stand up, get up, rise
- Chinese aliases: 站起来, 起立, 站起
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Stand up.

### static_walk

- Official SDK method: `StaticWalk`
- Risk level: `safe`
- English aliases: static walk
- Chinese aliases: 静态步态, 静态走
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Use static walk mode.

### status_report

- Official SDK method: `SportModeState`
- Risk level: `safe`
- English aliases: report status, status, battery
- Chinese aliases: 报告状态, 状态, 电量
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Read current robot status.

### stop

- Official SDK method: `StopMove`
- Risk level: `safe`
- English aliases: stop, stop moving, halt, freeze, emergency stop, do not move, don't move, hold still, stay still, stay there, stand still
- Chinese aliases: 停止, 停下, 别动, 立刻停止, 急停, 不要动, 原地待命, 原地别动, 保持不动, 停在原地, 别移动
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Emergency stop remains the highest-priority command.

### stretch

- Official SDK method: `Stretch`
- Risk level: `safe`
- English aliases: stretch, stretch body
- Chinese aliases: 伸展, 伸个懒腰
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Play the stretch motion.

### switch_avoid_mode

- Official SDK method: `SwitchAvoidMode`
- Risk level: `safe`
- English aliases: switch avoid mode, toggle avoid mode
- Chinese aliases: 切换避障模式, 切换避障
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `False`
- Reason: Switch obstacle avoidance mode.

### turn_left

- Official SDK method: `Move`
- Risk level: `safe`
- English aliases: turn left, left
- Chinese aliases: 左转, 向左转
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `True`
- Reason: Turn left slowly for a bounded duration.

### turn_right

- Official SDK method: `Move`
- Risk level: `safe`
- English aliases: turn right, right
- Chinese aliases: 右转, 向右转
- Mock enabled: `True`
- Real robot enabled: `True`
- Requires standing: `True`
- Reason: Turn right slowly for a bounded duration.

## Caution

### auto_recovery_set

- Official SDK method: `AutoRecoverySet`
- Risk level: `caution`
- English aliases: set auto recovery, enable auto recovery
- Chinese aliases: 设置自动恢复, 开启自动恢复
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Set auto-recovery option.

### classic_walk

- Official SDK method: `ClassicWalk`
- Risk level: `caution`
- English aliases: classic walk
- Chinese aliases: 经典步态, 经典走
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Classic walk mode.

### dance1

- Official SDK method: `Dance1`
- Risk level: `caution`
- English aliases: dance, dance one, dance 1
- Chinese aliases: 跳舞, 舞蹈一, 跳第一个舞
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Preset motion may need open space; real robot disabled by default.

### dance2

- Official SDK method: `Dance2`
- Risk level: `caution`
- English aliases: dance two, dance 2, second dance
- Chinese aliases: 舞蹈二, 跳第二个舞
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Preset motion may need open space; real robot disabled by default.

### euler

- Official SDK method: `Euler`
- Risk level: `caution`
- English aliases: euler, change attitude, adjust attitude
- Chinese aliases: 姿态调整, 欧拉角
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Attitude control needs explicit parameters and environment checks.

### free_walk

- Official SDK method: `FreeWalk`
- Risk level: `caution`
- English aliases: free walk
- Chinese aliases: 自由走, 自由步态
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Walking mode changes need operator supervision before real-robot enablement.

### pose

- Official SDK method: `Pose`
- Risk level: `caution`
- English aliases: pose, strike a pose
- Chinese aliases: 摆姿势, 姿势
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Enable pose preset.

### speed_level

- Official SDK method: `SpeedLevel`
- Risk level: `caution`
- English aliases: speed level, change speed
- Chinese aliases: 速度等级, 调整速度
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Voice must not freely increase speed level.

## Dangerous

### back_flip

- Official SDK method: `BackFlip`
- Risk level: `dangerous`
- English aliases: back flip, backflip, flip backward
- Chinese aliases: 后空翻, 向后翻, 后翻
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Dangerous back flip action; real robot disabled.

### cross_step

- Official SDK method: `CrossStep`
- Risk level: `dangerous`
- English aliases: cross step
- Chinese aliases: 交叉步
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Cross-step gait is disabled for real robot.

### free_bound

- Official SDK method: `FreeBound`
- Risk level: `dangerous`
- English aliases: free bound, bound
- Chinese aliases: 自由跳跃步态, 弹跳步态
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Dangerous bound gait; real robot disabled.

### free_jump

- Official SDK method: `FreeJump`
- Risk level: `dangerous`
- English aliases: free jump
- Chinese aliases: 自由跳
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Dangerous free jump mode; real robot disabled.

### front_flip

- Official SDK method: `FrontFlip`
- Risk level: `dangerous`
- English aliases: front flip, flip forward, forward flip
- Chinese aliases: 前空翻, 向前翻, 前翻
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Flip motion may cause falls, collisions, or hardware damage.

### front_jump

- Official SDK method: `FrontJump`
- Risk level: `dangerous`
- English aliases: jump, front jump, jump forward
- Chinese aliases: 跳, 跳跃, 向前跳
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Dangerous jump action; real robot disabled.

### front_pounce

- Official SDK method: `FrontPounce`
- Risk level: `dangerous`
- English aliases: pounce, front pounce, pounce forward
- Chinese aliases: 扑, 扑击, 向前扑
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Dangerous pounce action; real robot disabled.

### hand_stand

- Official SDK method: `HandStand`
- Risk level: `dangerous`
- English aliases: handstand, hand stand
- Chinese aliases: 倒立
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Dangerous handstand action; real robot disabled.

### left_flip

- Official SDK method: `LeftFlip`
- Risk level: `dangerous`
- English aliases: left flip, flip left
- Chinese aliases: 左翻, 向左翻
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Dangerous left flip action; real robot disabled.

### scrape

- Official SDK method: `Scrape`
- Risk level: `dangerous`
- English aliases: scrape
- Chinese aliases: 刮擦, scrape
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Official Scrape motion; treated as dangerous until behavior is confirmed.

### trot_run

- Official SDK method: `TrotRun`
- Risk level: `dangerous`
- English aliases: trot run, run fast, sprint
- Chinese aliases: 快跑, 高速跑, 小跑
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: High-speed running action; real robot disabled.

### walk_upright

- Official SDK method: `WalkUpright`
- Risk level: `dangerous`
- English aliases: walk upright, upright walk
- Chinese aliases: 直立行走, 直立走
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Upright walk is disabled for real robot.

## Disabled

### damp

- Official SDK method: `Damp`
- Risk level: `disabled`
- English aliases: damp
- Chinese aliases: 阻尼
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Mode semantics and physical behavior need a separate operator workflow.

### economic_gait

- Official SDK method: `EconomicGait`
- Risk level: `disabled`
- English aliases: economic gait
- Chinese aliases: 经济步态
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Disabled until local SDK method availability is confirmed.

### low_level_motor_control

- Official SDK method: `Low-level motor control`
- Risk level: `disabled`
- English aliases: low level control, motor control
- Chinese aliases: 低层控制, 电机控制
- Mock enabled: `False`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Official README warns low-level control conflicts with high-level sport service.

### move

- Official SDK method: `Move`
- Risk level: `disabled`
- English aliases: generic move
- Chinese aliases: 通用移动
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `True`
- Reason: Voice uses bounded directional Move derivatives with speed and duration limits.

### switch_joystick

- Official SDK method: `SwitchJoystick`
- Risk level: `disabled`
- English aliases: switch joystick, toggle joystick
- Chinese aliases: 切换手柄, 切换摇杆
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Control authority switches are not voice-enabled.

### trajectory_follow

- Official SDK method: `TrajectoryFollow`
- Risk level: `disabled`
- English aliases: trajectory follow, follow trajectory
- Chinese aliases: 轨迹跟踪, 跟随轨迹
- Mock enabled: `True`
- Real robot enabled: `False`
- Requires standing: `False`
- Reason: Requires validated trajectory input, not a single voice phrase.
