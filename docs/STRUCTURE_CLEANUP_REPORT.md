# Structure Cleanup Report

## Summary

This cleanup grouped entry scripts, documents, audit output, and runtime-generated
files without changing the core `src/` business modules.

## Moved

- `logs/` -> `runtime_data/logs/`
- `debug_audio/` -> `runtime_data/debug_audio/`
- `temp_audio/` -> `runtime_data/temp_audio/`
- `project_audit/` -> `audits/project_audit/`
- long-form guides -> `docs/`
- run scripts -> `scripts/run/`
- environment and status checks -> `scripts/check/`
- audio and Whisper test tools -> `scripts/test_tools/`
- model cache tools -> `scripts/model_tools/`

## Added

- `project_cli.py`
- `docs/COMMANDS.md`
- `docs/DEPENDENCIES.md`
- `docs/MODEL_MANAGEMENT.md`
- `docs/STRUCTURE_CLEANUP_REPORT.md`
- `_bootstrap.py` helpers in script subdirectories
- `runtime_data/*/.gitkeep`
- `audits/.gitkeep`

## Preserved

- `.venv/` was not deleted or copied into Git.
- `models/whisper/base.pt` was not deleted or moved.
- `src/` core modules were not reorganized.
- Real Go2 mode remains disabled by default.

## Verification

The following checks passed after cleanup:

```text
.venv\Scripts\python.exe -m compileall src scripts tests project_cli.py main.py
.venv\Scripts\python.exe project_cli.py status
.venv\Scripts\python.exe project_cli.py asr-check
.venv\Scripts\python.exe project_cli.py portable-check
.venv\Scripts\python.exe project_cli.py test
.venv\Scripts\python.exe project_cli.py gui --help
```

Unit tests:

```text
Ran 31 tests OK
```
