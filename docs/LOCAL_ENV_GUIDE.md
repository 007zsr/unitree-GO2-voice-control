# Local Environment Guide

This project should run from its own virtual environment and local model
directory. Do not copy Python packages from a system Python installation.

## Windows First Run

```bat
cd /d path\to\go2_voice_control
setup_windows_venv.bat
run_gui_windows.bat
```

The GUI should use:

```text
go2_voice_control\.venv\Scripts\python.exe
```

## Ubuntu / anbangtu First Run

Install system dependencies first:

```bash
sudo apt update
sudo apt install -y ffmpeg portaudio19-dev libsndfile1 python3-venv python3-tk
```

Then create the project virtual environment:

```bash
cd /path/to/go2_voice_control
bash setup_ubuntu_venv.sh
bash run_gui_ubuntu.sh
```

## Whisper Models

Whisper model weights are stored under:

```text
models/whisper/
```

The code passes this directory to `whisper.load_model(..., download_root=...)`.
If the model file is missing and the machine has network access, the first ASR
run will download the model into this directory.

For offline migration, copy the source tree and copy `models/whisper/` from a
prepared machine. Recreate `.venv` on the target OS instead of copying it.

## C Drive Cache Safety

The model collection scripts only scan known user cache directories and copy
confirmed model files into `models/`. They do not clean system locations, Python
packages, user cache folders, or registry entries.

C drive cache files remain at their original paths after collection. If cache
cleanup is ever needed, the user must review and handle it manually.

Useful commands:

```bat
.venv\Scripts\python.exe project_cli.py collect-models
.venv\Scripts\python.exe project_cli.py portable-check
```

## What Not To Commit

Do not commit:

```text
.venv/
models/whisper/*.pt
debug_audio/
logs/
temp_audio/
runtime_data/
audits/
```

Commit requirements files, setup scripts, configs, and documentation instead.

## Diagnostics

Check ASR dependencies:

```bat
.venv\Scripts\python.exe project_cli.py asr-check
```

Check runtime paths:

```bat
.venv\Scripts\python.exe project_cli.py status
```

Expected key lines:

```text
Is project venv: true
Whisper model directory: ...\go2_voice_control\models\whisper
ASR status: OK
```
