# Go2 Readonly Connection Report

## 1. Time

- Checked at: 2026-05-05 03:55:42 CST

## 2. Network interfaces

- candidate interface: `enx4cea41674695`
- interface IP: `192.168.123.222/24`
- wifi interface: `wlp0s20f3`, `10.19.115.103/21`
- default route: `default via 10.19.119.254 dev wlp0s20f3`
- Go2 route: `192.168.123.0/24 dev enx4cea41674695 proto kernel scope link src 192.168.123.222 metric 100`
- NetworkManager state: `enx4cea41674695` is ethernet / connected / `Wired connection 1`
- interfaces not used for SDK2: `wlp0s20f3`, `enp8s0`, `lo`

## 3. SDK environment

- python: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/.venv/bin/python`
- cyclonedds: OK
- unitree_sdk2py: OK
- SDK path: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/third_party/unitree_sdk2_python/unitree_sdk2py/__init__.py`

## 4. Ping / neighbor check

- `ip neigh show dev enx4cea41674695`:
  - `192.168.123.18 lladdr 3c:6d:66:61:54:0b STALE`
  - `192.168.123.161 lladdr 7e:1d:75:60:f5:89 STALE`
- `ping -c 3 -I enx4cea41674695 192.168.123.161`: OK
- ping result: 3 transmitted, 3 received, 0% packet loss
- ping notes: `192.168.123.161` is reachable through `enx4cea41674695`.

## 5. Official read_highstate.py

- expected command: `.venv/bin/python third_party/unitree_sdk2_python/example/high_level/read_highstate.py enx4cea41674695`
- result: FAIL / skipped
- error: current local `unitree_sdk2_python` checkout does not contain `third_party/unitree_sdk2_python/example/high_level/read_highstate.py`.
- local Go2 high-level example files found:
  - `third_party/unitree_sdk2_python/example/go2/high_level/go2_sport_client.py`
  - `third_party/unitree_sdk2_python/example/go2/high_level/go2_utlidar_switch.py`
- safety note: `go2_sport_client.py` is an interactive motion test and was not run.

## 6. Official wireless_controller.py

- command: `timeout 10s .venv/bin/python third_party/unitree_sdk2_python/example/wireless_controller/wireless_controller.py enx4cea41674695`
- result: FAIL / no sample output before timeout
- error: command timed out after 10 seconds with only the startup prompt printed.
- note: the Python example in this checkout has Go2 imports commented out and imports `unitree_hg` LowState by default, so it is not a clean Go2 wireless read for this setup without source adjustment.

## 7. Project go2 readonly check

- command: `.venv/bin/python project_cli.py go2-check --interface enx4cea41674695 --readonly`
- result: partial OK
- interface: OK, `enx4cea41674695 UP 192.168.123.222/24`
- SDK import: OK
- DDS init: OK
- high state read: OK, 3 samples from `rt/sportmodestate`
- wireless state read: FAIL, 0 samples from `rt/wirelesscontroller`
- sample high state fields:
  - `mode`: 0
  - `gait_type`: 0
  - `position`: approximately `[-0.00299, 0.00566, 0.31091]`
  - `body_height`: approximately `0.32038`
  - `error_code`: 100
- implementation note: project readonly script uses only `ChannelFactoryInitialize` and `ChannelSubscriber.Read()`. It does not import `SportClient`, create a motion client, publish DDS messages, or call any motion API.

## 8. Safety confirmation

- robot_mode: `mock`
- enable_real_robot: `false`
- motion command sent: no
- forbidden motion examples run: no
- `SportClient` motion API calls: no
- unit tests after script addition: OK, 66 tests

## 9. Conclusion

- readonly connection: partial
- successful:
  - `enx4cea41674695` is the Go2 candidate wired interface.
  - `192.168.123.161` is reachable by ping.
  - SDK import and CycloneDDS import are OK.
  - DDS init on `enx4cea41674695` is OK.
  - project readonly check can read Go2 high state from `rt/sportmodestate`.
  - no motion command was sent.
- not yet complete:
  - official `read_highstate.py` is not present in this local SDK checkout.
  - wireless controller state was not read from `rt/wirelesscontroller` during this check.
- next recommended step: repeat/extend read-only checks for wireless controller topic and decide whether the project readonly high-state check is an acceptable replacement for the missing official `read_highstate.py`. Do not start low-risk motion testing until that decision is made.
