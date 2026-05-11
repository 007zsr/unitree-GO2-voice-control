# Go2 SDK Install Report

## 1. Environment

- Ubuntu version: Ubuntu 26.04 LTS
- Python: Python 3.14.4
- Project path: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control`
- venv python: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control/.venv/bin/python`

## 2. System dependencies

- git: OK, `git version 2.53.0`
- cmake: system `cmake` not installed; project-local `.venv/bin/cmake` OK, `4.3.2`
- g++: OK, `15.2.0`
- make: OK, `4.4.1`
- note: no `sudo apt` was run from the restricted Codex session.

## 3. Python dependencies

- cyclonedds: OK, `0.10.2`
- numpy: OK, `2.4.4`
- opencv-python: OK, `4.13.0.92`
- unitree_sdk2py: OK, `1.0.1`, installed editable from `third_party/unitree_sdk2_python`
- pip dependency check: OK, no broken requirements found

## 4. Source repositories

- unitree_sdk2_python path: `third_party/unitree_sdk2_python`
- unitree_sdk2_python commit: `d9467c5fbe5428442048d4ebd2dec4b8f719a7c8`
- unitree_sdk2 path: `third_party/unitree_sdk2`
- unitree_sdk2 commit: `6d03531e109135b18500c7c3e6f8408ba857134e`
- unitree_ros2 path: `third_party/unitree_ros2`
- unitree_ros2 commit: `5204e6e098ee53f4bd929bd77eb1d387cd0fa842`
- cyclonedds path: `third_party/cyclonedds`
- cyclonedds commit: `5041f3560c088c99e5088b2b8520b69169621196`
- local Python headers: extracted under `third_party/python3.14-dev` from Ubuntu packages because system `python3.14-dev` was not installed.

## 5. Checks

- import `cyclonedds`: OK
- import `unitree_sdk2py`: OK
- import `SportClient`: OK
- scan SportClient: OK, 39 actions found
- go2-check: expected gate result; SDK imports OK, real robot connection refused because `robot_mode: mock` and `enable_real_robot: false`
- ASR check after SDK install: OK
- portable-check after SDK install: OK
- audio devices: OK, 10 input devices found
- unit tests after SDK install: OK, 66 tests
- fuzzy text test after SDK install: OK, total=260, complete=258, partial=2, serious=0, accuracy=99.23%
- generated scan report: `docs/GO2_OFFICIAL_ACTION_SCAN.md`
- generated catalog: `configs/go2_action_catalog.generated.yaml`
- action alignment report: `docs/GO2_SDK_ACTION_ALIGNMENT_REPORT.md`
- real robot mode: disabled

## 6. Safety status

- robot_mode: mock
- enable_real_robot: false
- motion commands sent: no
- ROS2 build or launch: not run
- low-level motor control: not run
