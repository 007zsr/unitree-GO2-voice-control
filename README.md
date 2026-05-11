# Unitree Go2 Voice Control

A voice-control software prototype for the Unitree Go2 robot dog.

The project is currently Mock-first. Real Go2 movement is disabled by default,
and the V1.1 release is intended for GUI, ASR, semantic parsing, LLM fallback
configuration, command planning, safety, queueing, and simulated execution
tests.

## Current Pipeline

Voice input -> Whisper speech recognition -> semantic engine -> command
planning -> safety check -> simulated execution

Implemented flow:

```text
GUI -> Whisper ASR -> NLU -> CommandPlan -> Safety -> CommandQueue -> MockAdapter
```

V1.1 keeps the default semantic engine in traditional mode and adds optional
LLM fallback plumbing behind the existing command planning and safety layers.
LLM output is parsed into CommandPlan-compatible intents and never calls the
robot adapter directly.

## Features

- GUI interface
- One-shot voice commands
- One-shot text commands
- Continuous listening
- Whisper ASR
- Rule-based NLU with Chinese, English, and mixed-language command support
- Semantic engine modes: traditional, llm_fallback, and llm_only_debug
- LLM provider base layer with mock provider tests
- Local Qwen provider availability checks without eager model loading
- Legacy config aliases for LLM fallback settings
- CommandPlan sequential commands
- Fuzzy command recognition
- Safety checks
- Emergency stop priority in the command queue
- Mock execution
- Structured logs
- Batch fuzzy text testing
- Project-local model directory support

## Safety

Real Go2 movement is disabled by default.

```yaml
robot_mode: mock
enable_real_robot: false
```

Do not enable real robot control until the preflight process in
`docs/REAL_ROBOT_PREFLIGHT.md` has been completed with a supervised robot,
clear surroundings, and a tested emergency stop path.

## Run on Windows

```bat
setup_windows_venv.bat
run_gui_windows.bat
```

## Run on Ubuntu / Anbangtu

```bash
sudo apt update
sudo apt install -y ffmpeg portaudio19-dev libsndfile1 python3-venv python3-tk
bash setup_ubuntu_venv.sh
bash run_gui_ubuntu.sh
```

## Run Tests

```bat
.venv\Scripts\python.exe project_cli.py test
.venv\Scripts\python.exe project_cli.py fuzzy-text-test
```

## Models

Large model files are not committed to normal Git. Place Whisper model files
under:

```text
models/whisper/
```

For example, a local Whisper model may exist as `models/whisper/base.pt`, but it
is intentionally ignored by Git. If model distribution is needed, attach the
model to a GitHub Release or use Git LFS after explicitly enabling that
workflow.

Local Qwen model directories, when used, belong under:

```text
models/qwen/
```

Qwen model detection is read-only. Unit tests use mock providers and do not run
real Qwen inference.

## Directory Map

- `src/`: core source code.
- `configs/`: runtime configuration.
- `scripts/`: grouped helper scripts.
- `models/`: local model directories and model placement notes.
- `runtime_data/`: local logs, debug audio, and temporary audio.
- `docs/`: setup, operation, release, and safety guides.
- `tests/`: automated tests.

More commands are listed in `docs/COMMANDS.md`. Environment details are in
`docs/LOCAL_ENV_GUIDE.md`.

## Version

Current version: v1.1.0
