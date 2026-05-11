# Go2 Real Action No Response Diagnosis

## 1. Time

- Updated: 2026-05-05

## 2. Network

- interface: `enx4cea41674695`
- IP: `192.168.123.222/24` from prior readonly check
- ping: prior check OK to `192.168.123.161`
- high state: prior readonly project check OK

## 3. Last project action logs

### sit_down

- command_id: `cmd_20260505_040717_01d6f7`
- NLU: `sit_down`
- Safety: allowed
- Adapter: `MockAdapter`
- SDK method: none
- SDK return: none
- observed robot behavior: no real motion expected from this log

### stand_up

- command_id: `cmd_20260505_040617_0b35b4` among recent stand-up logs
- NLU: `stand_up`
- Safety: allowed
- Adapter: `MockAdapter`
- SDK method: none
- SDK return: none
- observed robot behavior: no real motion expected from this log

## 4. Config check

- `configs/app.yaml`: `robot_mode: mock`, `enable_real_robot: false`
- `configs/go2.yaml`: `robot_mode: mock`, `enable_real_robot: false`
- Persistent defaults are safe and unchanged.
- Real action tests must use CLI in-memory overrides, not permanent config edits.

## 5. Go2Adapter debug

- Debug logging added to `src/robot/go2_adapter.py`.
- Log path: `runtime_data/logs/go2_adapter_debug/go2_adapter_debug.jsonl`
- Captured fields include:
  - `Go2Adapter.execute START`
  - `command_id`
  - `intent`
  - `sdk_method`
  - `interface`
  - `robot_mode`
  - `enable_real_robot`
  - `sport_client_initialized`
  - `request_args`
  - `sdk_return_code`
  - `sdk_return_message`
  - `Go2Adapter.execute END`
- No real Go2Adapter action was executed during this update.

## 6. Dry-run project chain checks

### sit_down

- command: `project_cli.py real-action-test --interface enx4cea41674695 --text "sit down" --allow-only sit_down,stand_up,rise_sit --debug-adapter --dry-run`
- NLU: OK, `sit_down`
- catalog SDK method: `Sit`
- stage precheck: allowed
- motion command sent: no

### stand_up

- command: `project_cli.py real-action-test --interface enx4cea41674695 --text "stand up" --allow-only sit_down,stand_up,rise_sit --debug-adapter --dry-run`
- NLU: OK, `stand_up`
- catalog SDK method: `StandUp`
- actual Go2Adapter preference for this test: `RiseSit` when available, otherwise `StandUp`
- stage precheck: allowed
- motion command sent: no

### non-whitelist guard

- command: `turn right`
- NLU: `turn_right`
- result: rejected before runtime start
- reason: `Rejected: action not allowed in this real robot test stage`
- motion command sent: no

## 7. Direct SDK comparison

- Script added: `scripts/run/go2_direct_posture_test.py`
- Allowed direct actions only: `sit`, `rise`, `standup`
- Required confirmation: `I_UNDERSTAND_THIS_WILL_CONTROL_GO2`
- Direct SDK comparison was not run in this update.

## 8. High state before / after

- Old action logs did not capture high state before/after.
- Updated `real-action-test` captures `before_state` and `after_state` for actual confirmed runs.
- Dry-run checks do not capture high state because no runtime connection is started.

## 9. Diagnosis checklist

- [x] Current persistent config is still Mock mode.
- [x] Existing recent sit/stand logs show `MockAdapter`, not `Go2Adapter`.
- [x] `sit_down` parses correctly.
- [x] `stand_up` parses correctly.
- [x] Stage whitelist rejects non-sit/stand actions.
- [x] Actual confirmed `Go2Adapter` run has been performed for `sit_down`.
- [x] SDK return code for real `Sit` is known: `0`.
- [x] High state changed after `Sit`.
- [ ] Whether direct SDK posture command moves the robot is still unknown.

## 10. Diagnosis

The strongest finding from existing logs is that the visible recent sit/stand commands went through `MockAdapter`. Those runs could not have moved the real robot.

The project chain is now prepared to distinguish the remaining cases:

- If actual confirmed `real-action-test` logs no `Go2Adapter.execute START`, the CLI/runtime override is still wrong.
- If `Go2Adapter.execute START` appears but there is no `sdk_call`, the queue/adapter branch is wrong.
- If `sdk_call END` returns a nonzero code, this is an SDK/request failure.
- If SDK returns `0` or `None` and the robot still does not move, compare with the guarded direct SDK script to separate project-chain issues from robot/SDK/high-level-service issues.

## 11. Recommended fix

Run the next diagnostic as a single confirmed real action only after the site checklist is true:

```bash
.venv/bin/python project_cli.py real-action-test \
  --interface enx4cea41674695 \
  --text "sit down" \
  --allow-only sit_down,stand_up,rise_sit \
  --debug-adapter \
  --confirm-site-ready \
  --observed "no response / moved as expected / other"
```

Then inspect:

```bash
tail -100 runtime_data/logs/go2_adapter_debug/go2_adapter_debug.jsonl
tail -20 runtime_data/reports/go2_real_basic_action_test_01_runs.jsonl
```

If the project chain enters `Go2Adapter` and SDK returns success but the robot still does not move, run the guarded direct comparison separately:

```bash
.venv/bin/python scripts/run/go2_direct_posture_test.py \
  --interface enx4cea41674695 \
  --action sit \
  --confirm I_UNDERSTAND_THIS_WILL_CONTROL_GO2
```

## 12. Real Go2Adapter sit_down diagnostic 01

### Command

```bash
.venv/bin/python project_cli.py real-action-test \
  --interface enx4cea41674695 \
  --text "sit down" \
  --allow-only sit_down \
  --debug-adapter \
  --confirm-site-ready \
  --observed "pending user observation"
```

### Project chain result

- command_id: `cmd_20260505_042144_d03a1b`
- NLU: `sit_down`
- Safety: allowed
- Adapter selected: `Go2Adapter`
- runtime robot_mode: `go2`
- runtime enable_real_robot: `true`
- interface: `enx4cea41674695`
- SportClient initialized: true
- SDK method: `Sit`
- SDK return: `0`
- SDK message: `OK`
- motion command sent: yes
- non-whitelist action sent: no
- dangerous action sent: no

### Go2Adapter debug log

- log: `runtime_data/logs/go2_adapter_debug/go2_adapter_debug.jsonl`
- `Go2Adapter.connect START`: recorded
- `Go2Adapter.connect END`: success, `state_subscriber_initialized=true`
- `Go2Adapter.execute START`: `intent=sit_down`
- `Go2Adapter.sdk_call START`: `sdk_method=Sit`
- `Go2Adapter.sdk_call END`: `sdk_return_code=0`
- `Go2Adapter.execute END`: success

### High state before / after

Before:

- `error_code`: `100`
- `body_height`: `0.3204260468482971`
- `position`: `[-0.002513373037800193, 0.004841463174670935, 0.3109232485294342]`
- `rpy`: `[-0.037743277847766876, -0.0030745440162718296, -0.15509270131587982]`

After:

- `error_code`: `1007`
- `body_height`: `0.22105050086975098`
- `position`: `[0.09818629920482635, -0.027345934882760048, 0.22256308794021606]`
- `rpy`: `[-0.0029979392420500517, -0.8581733703613281, -0.20108774304389954]`

Conclusion:

- High state changed significantly after `Sit`.
- Telemetry is consistent with a posture transition into sit/down state.
- Visual observation still depends on the user at the robot site.

### Default config after test

- `configs/app.yaml`: `robot_mode: mock`, `enable_real_robot: false`
- `configs/go2.yaml`: `robot_mode: mock`, `enable_real_robot: false`

## 13. Real Go2Adapter stand_up diagnostic 01

### Command

```bash
.venv/bin/python project_cli.py real-action-test \
  --interface enx4cea41674695 \
  --text "stand up" \
  --allow-only stand_up \
  --debug-adapter \
  --confirm-site-ready \
  --observed "pending user observation"
```

### Project chain result

- command_id: `cmd_20260505_042359_21f070`
- NLU: `stand_up`
- Safety: allowed
- Adapter selected: `Go2Adapter`
- runtime robot_mode: `go2`
- runtime enable_real_robot: `true`
- interface: `enx4cea41674695`
- SportClient initialized: true
- SDK method: `RiseSit`
- SDK return: `0`
- SDK message: `OK`
- motion command sent: yes
- non-whitelist action sent: no
- dangerous action sent: no

### Go2Adapter debug log

- log: `runtime_data/logs/go2_adapter_debug/go2_adapter_debug.jsonl`
- `Go2Adapter.connect START`: recorded
- `Go2Adapter.connect END`: success, `state_subscriber_initialized=true`
- `Go2Adapter.execute START`: `intent=stand_up`
- `Go2Adapter.sdk_call START`: `sdk_method=RiseSit`
- `Go2Adapter.sdk_call END`: `sdk_return_code=0`
- `Go2Adapter.execute END`: success

### High state before / after

Before:

- `error_code`: `1007`
- `body_height`: `0.2212156057357788`
- `position`: `[0.09652914851903915, -0.02711237035691738, 0.22252625226974487]`
- `rpy`: `[-0.0008864772971719503, -0.8651170134544373, -0.20293016731739044]`

After:

- `error_code`: `1013`
- `body_height`: `0.3225535452365875`
- `position`: `[0.17893017828464508, -0.08466417342424393, 0.31122446060180664]`
- `rpy`: `[0.03744959831237793, 0.013731959275901318, -0.26915445923805237]`

Conclusion:

- High state changed significantly after `RiseSit`.
- Telemetry is consistent with a transition from sitting/down posture back to standing height.
- Visual observation still depends on the user at the robot site.

### Default config after test

- `configs/app.yaml`: `robot_mode: mock`, `enable_real_robot: false`
- `configs/go2.yaml`: `robot_mode: mock`, `enable_real_robot: false`
