# Project Structure Cleanup Plan

This cleanup is intentionally low risk. It does not remove `.venv/`, model
files, C drive files, source files, or runtime artifacts. Existing runtime
artifacts are moved into clearer directories, and lightweight files that will be
moved are backed up first.

## Files And Directories To Move

Runtime artifacts:

- `logs/` -> `runtime_data/logs/`
- `debug_audio/` -> `runtime_data/debug_audio/`
- `temp_audio/` -> `runtime_data/temp_audio/`

Audit output:

- `project_audit/` -> `audits/project_audit/`

Scripts:

- `scripts/run_gui.py` -> `scripts/run/run_gui.py`
- `scripts/run_text_demo.py` -> `scripts/run/run_text_demo.py`
- `scripts/run_mock_demo.py` -> `scripts/run/run_mock_demo.py`
- `scripts/check_asr_env.py` -> `scripts/check/check_asr_env.py`
- `scripts/check_anbangtu_env.py` -> `scripts/check/check_anbangtu_env.py`
- `scripts/check_go2_connection.py` -> `scripts/check/check_go2_connection.py`
- `scripts/check_portable_project.py` -> `scripts/check/check_portable_project.py`
- `scripts/check_runtime_paths.py` -> `scripts/check/check_runtime_paths.py`
- `scripts/list_audio_devices.py` -> `scripts/check/list_audio_devices.py`
- `scripts/test_record_audio.py` -> `scripts/test_tools/test_record_audio.py`
- `scripts/test_whisper_file.py` -> `scripts/test_tools/test_whisper_file.py`
- `scripts/scan_existing_models_readonly.py` -> `scripts/model_tools/scan_existing_models_readonly.py`
- `scripts/collect_whisper_models.py` -> `scripts/model_tools/collect_whisper_models.py`
- `scripts/collect_qwen_models.py` -> `scripts/model_tools/collect_qwen_models.py`
- `scripts/model_cache_utils.py` -> `scripts/model_tools/model_cache_utils.py`

Documents:

- `LOCAL_ENV_GUIDE.md` -> `docs/LOCAL_ENV_GUIDE.md`
- `WINDOWS_RUN_GUIDE.md` -> `docs/WINDOWS_RUN_GUIDE.md`
- `UBUNTU_RUN_GUIDE.md` -> `docs/UBUNTU_RUN_GUIDE.md`
- `REAL_ROBOT_PREFLIGHT.md` -> `docs/REAL_ROBOT_PREFLIGHT.md`
- `model_migration_report.md` -> `docs/model_migration_report.md`

## Files To Keep In Place

- `.venv/`
- `models/whisper/base.pt`
- `src/`
- `configs/`
- `tests/`
- `requirements*.txt`
- `README.md`
- `.env.example`
- `.gitignore`
- `setup_windows_venv.bat`
- `setup_ubuntu_venv.sh`
- `run_gui_windows.bat`
- `run_gui_ubuntu.sh`

## New Files To Add

- `project_cli.py`
- `docs/COMMANDS.md`
- `docs/DEPENDENCIES.md`
- `docs/MODEL_MANAGEMENT.md`
- helper `_bootstrap.py` files in script subdirectories
- `runtime_data/**/.gitkeep`

## Backup

Before moving, the cleanup creates `backup_before_structure_cleanup/` and copies
only lightweight files/directories that are about to move. It does not copy
`.venv/` or large model weights.

## Safety Notes

- No delete, clean, or uninstall operation is part of this plan.
- No C drive file is touched.
- Go2 real robot settings stay mock/off.
- `src/robot/go2_adapter.py` stays in place.
