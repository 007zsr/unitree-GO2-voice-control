# GitHub Upload Report - v1.1.0

## Target

- Repository: `007zsr/unitree-GO2-voice-control`
- Release branch: `release/v1.1`
- Tag: `v1.1.0`
- Release title: `V1.1 - Qwen / LLM fallback semantic engine`

## Source And Release Worktree

- Source project: `/home/sirui-zhou/VS_code/unitree-GO2-voice-control`
- Release worktree: `/home/sirui-zhou/VS_code/github_release_work/unitree-GO2-voice-control`
- Remote base branch: `main`
- Previous tag detected: `v1.0.0`

## Sync Rules

The release worktree was populated from the source project with `rsync --delete`.
The sync excluded local virtual environments, Python caches, runtime data,
temporary files, local agent metadata, external SDK/source checkouts, and model
binary formats.

Excluded examples:

- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `runtime_data/`
- `third_party/`
- `.agents/`
- `.codex/`
- `*.pt`
- `*.bin`
- `*.safetensors`
- `*.gguf`
- `*.wav`
- `*.log`

## Large File Check

- Source local model detected: `models/whisper/base.pt`, 139 MiB.
- The Whisper model file is intentionally not synced into the release worktree.
- Release worktree files larger than 50 MiB: none.
- Release worktree files larger than 100 MiB: none.
- Git LFS was not required for the V1.1 code release.

If model delivery is required, publish model files as GitHub Release assets or
enable Git LFS intentionally before tracking model binaries.

## Validation

- `compileall -q src tests`: passed.
- Focused unittest modules:
  - `tests.test_local_qwen_provider`
  - `tests.test_semantic_parser`
  - `tests.test_command_flow`
  - `tests.test_llm_fallback`
- Combined focused test result: `Ran 28 tests`, `OK`.
- Source project portable check: `PORTABLE_OK`.
- Release worktree portable check with the external source `.venv`:
  `PORTABLE_WARN`, expected because `.venv` is intentionally excluded from Git.
- Encoding scan: `DECODE_ERRORS 0`, `BAD_TOKENS 0`.
- Process check: `NO_TEST_PROCESSES`.

## Safety Notes

- No force push was used.
- Real Go2 was not touched during release validation.
- Real Qwen inference was not loaded during unit tests.
- LLM fallback remains behind CommandPlan, SafetyController, CommandQueue, and Adapter boundaries.
