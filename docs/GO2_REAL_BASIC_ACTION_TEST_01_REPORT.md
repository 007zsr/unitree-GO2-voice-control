# Go2 Real Basic Action Test 01 Report

## 1. Time

- Report updated from `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/runtime_data/reports/go2_real_basic_action_test_01_runs.jsonl`

## 2. Environment

- Project path: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control`
- Interface: `enx4cea41674695`
- IP: `192.168.123.222/24`
- SDK: `unitree_sdk2py` from project `.venv` / `third_party/unitree_sdk2_python`
- CycloneDDS: OK from prior SDK import/read-only checks

## 3. Safety settings

- robot_mode during test: `go2` in memory only
- enable_real_robot during test: `true` in memory only
- allowed actions: `sit_down`, `stand_up`, `rise_sit`
- continuous listening: disabled / not used by this command
- dangerous actions: not allowed
- disconnect behavior: `stop_on_disconnect=false` for this stage to avoid implicit StopMove

## 4. Text sit_down test

- input: `sit down`
- transcript: `sit down`
- intent: `sit_down`
- Safety: `allowed`
- SDK method: `Sit`
- result: `OK`
- adapter message: `Go2 sit_down via Sit returned 0`
- observed robot behavior: `pending user observation`
- before high state: `{"mode": 0, "gait_type": 0, "progress": 0.0, "position": [-0.002513373037800193, 0.004841463174670935, 0.3109232485294342], "velocity": [1.476053834714719e-09, -1.1145556477742957e-08, 3.1069552619555907e-07], "yaw_speed": -0.009587379172444344, "body_height": 0.3204260468482971, "error_code": 100}`
- after high state: `{"mode": 0, "gait_type": 0, "progress": 0.0, "position": [0.09818629920482635, -0.027345934882760048, 0.22256308794021606], "velocity": [-2.3362619572253607e-07, -1.175451541657324e-10, -1.9698109099408612e-07], "yaw_speed": 0.0010652643395587802, "body_height": 0.22105050086975098, "error_code": 1007}`

## 5. Text stand_up test

- input: `stand up`
- transcript: `stand up`
- intent: `stand_up`
- Safety: `allowed`
- SDK method: `RiseSit`
- result: `OK`
- adapter message: `Go2 stand_up via RiseSit returned 0`
- observed robot behavior: `pending user observation`
- before high state: `{"mode": 0, "gait_type": 0, "progress": 0.0, "position": [0.09652914851903915, -0.02711237035691738, 0.22252625226974487], "velocity": [-2.3267760695944162e-07, 1.5792330776420727e-09, -1.9595184141962818e-07], "yaw_speed": 0.009587379172444344, "body_height": 0.2212156057357788, "error_code": 1007}`
- after high state: `{"mode": 0, "gait_type": 0, "progress": 0.0, "position": [0.17893017828464508, -0.08466417342424393, 0.31122446060180664], "velocity": [-9.957316251529846e-07, 2.850210648830398e-06, 7.58881215006113e-05], "yaw_speed": 0.008522114716470242, "body_height": 0.3225535452365875, "error_code": 1013}`

## 6. Voice sit_down test

- result: not executed

## 7. Voice stand_up test

- result: not executed

## 8. Rejected commands

- text: `turn right` -> Rejected: action not allowed in this real robot test stage
- text: `turn right` -> Rejected: action not allowed in this real robot test stage

## 9. Unexpected behavior

- none recorded by script

## 10. Final status

- robot_mode restored: `mock` in config files
- enable_real_robot restored: `false` in config files
- can continue to next test: `yes`
