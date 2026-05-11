# Ubuntu Deploy Report

## 1. System

- User: sirui-zhou
- Project path: /home/sirui-zhou/VS_code/unitree-GO2-voice-control
- Generated at: 2026-05-05 Asia/Shanghai
- Rechecked at: 2026-05-05 Asia/Shanghai
- Python: Python 3.14.4
- Git version: git version 2.53.0
- ffmpeg: ffmpeg version 8.0.1-3ubuntu2
- System package install: completed manually by user outside the restricted Codex session

## 2. Git

- Repository: https://github.com/007zsr/unitree-GO2-voice-control
- Version/tag: v1.0.0
- Source used: GitHub v1.0.0 archive download
- Tag object: 99164024b9f44b5b385610330d8bbb425d62ee49
- Commit: fc547cba8cd40ee1d9c5b950110166ec4def9345
- Worktree status: not available because deployment used a tag archive rather than `git clone`

## 3. Virtual Environment

- Python executable: /home/sirui-zhou/VS_code/unitree-GO2-voice-control/.venv/bin/python
- Python from project .venv: yes
- pip packages installed: yes
- pip: 25.3
- Note: system `python3.14-venv` / ensurepip was missing, so pip was bootstrapped inside the project `.venv`.

## 4. Models

- Whisper model path: /home/sirui-zhou/VS_code/unitree-GO2-voice-control/models/whisper/base.pt
- Whisper model present: yes
- Qwen model path: /home/sirui-zhou/VS_code/unitree-GO2-voice-control/models/qwen
- Qwen local enabled: no (`rule_based`)

## 5. Checks

- Dependency imports:
  - whisper: OK
  - soundfile: OK
  - sounddevice: OK when run outside sandbox; sandboxed checks cannot connect to PipeWire/PulseAudio
  - tkinter: OK
- ASR check: OK
- Portable check: OK
- Unit tests: PASS, 66 tests
- Fuzzy text batch test: PASS, total=260, complete=258, partial=2, serious=0, accuracy=99.23%
- Audio devices: OK when run outside sandbox; 7 input devices found
- Microphone recording: OK, 5 second sample recorded, non-silent
- One-shot voice ASR sample: FAIL, Whisper executed but returned empty text / `no_speech`
- GUI launch: OK, started without errors and was stopped by timeout after entering the event loop
- Text command smoke tests:
  - `Stand up please.`: accepted, `stand_up`, Mock executed
  - `Come here.`: rejected/confirmation, `unknown_relative_move`, not submitted
  - `Do a front flip.`: rejected/confirmation, dangerous `front_flip`, not submitted
  - `Turn right and then turn left.`: accepted, `turn_right -> turn_left`, Mock executed

## 6. Safety

- robot_mode: mock
- enable_real_robot: false
- Go2 real robot motion: not enabled and not executed

## 7. Known Issues

- `sudo apt update && sudo apt install ...` still cannot run inside this restricted Codex session, but the user has installed the needed system packages from a normal Ubuntu terminal.
- Sandboxed commands cannot connect to PipeWire/PulseAudio, but non-sandboxed checks can enumerate audio devices.
- The microphone records non-silent audio, but the captured samples were not recognized as speech by Whisper (`no_speech_prob: 1.000`). One-shot voice and continuous listening still need a live spoken GUI/terminal check with the correct input device selected.
- The project was deployed from the v1.0.0 archive rather than `git clone`; `git` is now installed, but this directory is still not a `.git` worktree.

## 8. Next Steps

Run the final live voice checks from the Ubuntu desktop GUI:

```bash
cd /home/sirui-zhou/VS_code/unitree-GO2-voice-control
.venv/bin/python project_cli.py audio-devices
bash run_gui_ubuntu.sh
```

Then use the GUI one-shot voice and continuous listening buttons while speaking clearly into the selected input device.

## System dependency recheck

- git: OK
- ffmpeg: OK
- python3-tk: OK
- PortAudio / sounddevice: OK outside sandbox
- libsndfile / soundfile: OK

## Project checks

- ASR check: OK
- Audio devices: OK outside sandbox; 7 input devices found
- GUI launch: OK
- Unit tests: OK, 66 tests
- Fuzzy text test: OK, total=260, complete=258, partial=2, serious=0, accuracy=99.23%

## Final deployment status

- Text control: OK
- Voice one-shot: FAIL / needs live speech recheck, recorded samples were non-silent but Whisper returned no speech
- Continuous listening: FAIL / needs live speech recheck
- Mock execution: OK
- Real Go2: NOT ENABLED

## Unitree SDK2 dependency preparation

- unitree_sdk2_python: installed, editable from `third_party/unitree_sdk2_python`
- cyclonedds: OK, Python package `0.10.2`; local CycloneDDS C library built under `third_party/cyclonedds/install`
- numpy: OK, `2.4.4`
- opencv-python: OK, `4.13.0.92`
- unitree_sdk2 source: downloaded, `third_party/unitree_sdk2`
- unitree_ros2 source: downloaded for reference only, not built
- SportClient scan: OK, 39 Go2 actions found from local SDK source
- Generated SDK scan report: `docs/GO2_OFFICIAL_ACTION_SCAN.md`
- Generated SDK catalog: `configs/go2_action_catalog.generated.yaml`
- Action alignment report: generated, `docs/GO2_SDK_ACTION_ALIGNMENT_REPORT.md`
- SDK install report: generated, `docs/GO2_SDK_INSTALL_REPORT.md`
- go2-check: expected gate result; SDK imports OK, real robot connection refused because `robot_mode: mock` and `enable_real_robot: false`
- Post-SDK regression:
  - ASR check: OK
  - portable-check: OK
  - audio devices: OK, 10 input devices found
  - unit tests: OK, 66 tests
  - fuzzy text test: OK, total=260, complete=258, partial=2, serious=0, accuracy=99.23%
- Real robot enabled: false
- Motion command sent: no
- Note: system `cmake` is not installed in this restricted environment; `.venv/bin/cmake` was installed and used for the local CycloneDDS build.
