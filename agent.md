# go2_voice_control Agent Rules

## 1. Project Goal

Build and maintain a safe, Mock-first Unitree Go2 voice-control console.
The only control chain is:

```text
GUI / input
 -> SessionRuntime
 -> ASR / NLU
 -> RobotCommand
 -> Safety
 -> CommandQueue
 -> Adapter
```

## 2. Forbidden Actions

- Do not execute real Go2 motion during ordinary development.
- Do not enable real robot mode by default.
- Do not bypass `SessionRuntime`, `SafetyController`, or `CommandQueue`.
- Do not let GUI code call `Go2Adapter` or Unitree SDK directly.
- Do not delete `.venv/`, model files, C drive caches, logs, or debug audio without a separate explicit cleanup task.
- Do not record API keys, tokens, passwords, raw microphone streams, or large raw model outputs in logs.

## 3. Fixed Directories

- Source code: `src/`
- Config: `configs/`
- Scripts: `scripts/`
- Models: `models/`
- Runtime data: `runtime_data/`
- Logs: `runtime_data/logs/`
- Documentation: `docs/`
- Audit output: `audits/`

## 4. Logging System Rules

- The logging root is `runtime_data/logs/`.
- GUI sessions write to `runtime_data/logs/gui_sessions/`.
- One-shot text and one-shot voice tasks write to `runtime_data/logs/one_shot/`.
- Continuous listening writes to `runtime_data/logs/continuous/`.
- Errors are summarized in `runtime_data/logs/errors/`.
- Log indexes are written to `runtime_data/logs/index/log_index.jsonl`.
- Every GUI launch must have a `session_id`.
- Every user task must have a `command_id`.
- Every continuous listening run must have a `listen_id`; every chunk should have a chunk record.
- Logs record transcript text, semantic result, RobotCommand, Safety decision, queue result, adapter result, error stage, and error message.
- Logs may record relative debug audio paths, but not raw audio data or waveform content.
- Safety rejections are normal control outcomes, not system errors. Record them as `stage=safety` / `status=rejected` or `stage=safety_rejected`, and do not write them to error summaries.
- Ambiguous ASR/NLU rejections and strict-mode rejections should be visible in logs with stable reasons such as `ambiguous_asr_turn_left` or `single_direction_word_rejected_in_strict_mode`.
- Do not write scattered ad hoc log files from GUI code. Use `PipelineLogger`.
- Logging is observational only; it must not change Safety, Queue, or Adapter decisions.

## 5. Common Commands

Windows:

```bat
run_gui_windows.bat
.venv\Scripts\python.exe project_cli.py status
.venv\Scripts\python.exe project_cli.py asr-check
.venv\Scripts\python.exe project_cli.py logs --last 5
.venv\Scripts\python.exe project_cli.py test
```

Ubuntu:

```bash
bash run_gui_ubuntu.sh
.venv/bin/python project_cli.py status
.venv/bin/python project_cli.py asr-check
.venv/bin/python project_cli.py logs --last 5
.venv/bin/python project_cli.py test
```

## 6. Model Management Rules

- Whisper models belong in `models/whisper/`.
- Qwen local models belong in `models/qwen/`.
- Do not hardcode `C:\`, `D:\`, `/home`, or user-specific cache paths in business code.
- Model collection scripts may copy confirmed model files, but must never delete source cache files.

## 7. Go2 Real Robot Safety Rules

- Default config must remain `robot_mode: mock` and `enable_real_robot: false`.
- Real mode requires explicit config, SDK checks, network checks, emergency-stop checks, and human supervision.
- First-stage control is high-level motion only. Low-level motor control is forbidden.

## 8. C Drive Scan Safety Rules

- C drive cache scans are read-only.
- Allowed operations: list, inspect size, hash, copy confirmed model files.
- Forbidden operations: delete, move, rename, clean, uninstall, remove cache directories.

## 9. Git / Large File Rules

- Do not commit `.venv/`.
- Do not commit large model weights through ordinary Git.
- Do not commit runtime logs, debug audio, temporary audio, or audit output by default.
- Use requirements files, setup scripts, documentation, Release artifacts, or Git LFS for portable distribution.

## 10. Checks Before Code Changes

- Confirm the project root is `go2_voice_control`.
- Read the existing module before editing.
- Keep business logic in `src/`; keep commands in `project_cli.py` as routing only.
- Run at least:

```bat
.venv\Scripts\python.exe project_cli.py test
.venv\Scripts\python.exe project_cli.py asr-check
```

when changes touch runtime, GUI, logging, or ASR behavior.
