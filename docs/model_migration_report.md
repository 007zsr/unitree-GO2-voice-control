# Model Migration Report

Scan time: 2026-04-28T13:45:22

## Scanned Directories

- User-level Whisper cache directory

## Whisper Candidates

- `base.pt` (145262807 bytes)

## Project Model Directory

- Whisper model target: `models/whisper/base.pt`
- The project-local model file is intentionally ignored by normal Git.

## Qwen Candidates

- No confirmed local Qwen model directory was found.

## Source File Handling

Source model files were not deleted. If cleanup is needed, remove local cache
files manually after confirming they are no longer needed.

## Follow-up Recommendation

- Use `project_cli.py portable-check` or
  `scripts/check/check_portable_project.py` to check portable project status.
- Do not commit `.venv` or large model weights to normal Git.
