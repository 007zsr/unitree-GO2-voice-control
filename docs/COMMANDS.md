# Command Reference

Run these commands from the `go2_voice_control` project root.

## Windows

```bat
setup_windows_venv.bat
run_gui_windows.bat
.venv\Scripts\python.exe project_cli.py status
.venv\Scripts\python.exe project_cli.py asr-check
.venv\Scripts\python.exe project_cli.py portable-check
.venv\Scripts\python.exe project_cli.py test
.venv\Scripts\python.exe project_cli.py audio-devices
.venv\Scripts\python.exe project_cli.py record-test
.venv\Scripts\python.exe project_cli.py whisper-test --audio runtime_data\debug_audio\last_record.wav
.venv\Scripts\python.exe project_cli.py collect-models
.venv\Scripts\python.exe project_cli.py go2-check
.venv\Scripts\python.exe project_cli.py scan-go2-actions
.venv\Scripts\python.exe project_cli.py audit
.venv\Scripts\python.exe project_cli.py logs --last 5
.venv\Scripts\python.exe project_cli.py logs --errors
```

## Ubuntu / anbangtu

```bash
bash setup_ubuntu_venv.sh
bash run_gui_ubuntu.sh
.venv/bin/python project_cli.py status
.venv/bin/python project_cli.py asr-check
.venv/bin/python project_cli.py portable-check
.venv/bin/python project_cli.py test
.venv/bin/python project_cli.py audio-devices
.venv/bin/python project_cli.py record-test
.venv/bin/python project_cli.py whisper-test --audio runtime_data/debug_audio/last_record.wav
.venv/bin/python project_cli.py collect-models
.venv/bin/python project_cli.py go2-check
.venv/bin/python project_cli.py scan-go2-actions
.venv/bin/python project_cli.py audit
.venv/bin/python project_cli.py logs --last 5
.venv/bin/python project_cli.py logs --errors
```

## Notes

- `project_cli.py` is only a command router. It does not implement robot control logic.
- `go2-check` is intended for connection/status checks. It does not issue motion commands by default.
- `scan-go2-actions` scans the official Go2 SportClient source and writes the generated action scan report/catalog.
- `collect-models` may copy confirmed model files into `models/`, but it never deletes source cache files.
- The formal GUI entry points are `run_gui_windows.bat` and `run_gui_ubuntu.sh`.
- `logs` is read-only and prints recent log index or error entries.
- Safety rejections are expected control outcomes and should appear as `safety_rejected`, not as system errors.
- Strict command detection rejects isolated direction words such as `Right.` or `Left.`; use explicit phrases such as `Turn right.` or `Go2, right.`.
