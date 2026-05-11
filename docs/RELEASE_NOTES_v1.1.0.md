# V1.1 - Qwen / LLM fallback semantic engine

This release adds a configurable semantic engine layer for the Unitree Go2 voice-control project.

## Highlights

- Added semantic engine modes:
  - traditional
  - llm_fallback
  - llm_only_debug
- Added LLM provider base layer.
- Added mock provider for safe fallback tests.
- Added Local Qwen provider availability checks.
- Added config alias compatibility:
  - mock_llm -> mock
  - local_model_dir -> local_llm_model_dir
  - fallback_min_confidence -> llm_fallback_min_confidence
- Invalid semantic mode now safely falls back to traditional mode.
- LLM fallback remains behind rule/fuzzy semantic recognition.
- LLM output does not bypass CommandPlan, SafetyController, CommandQueue, or Adapter.

## Safety

- Default mode remains traditional.
- LLM is disabled by default.
- Real Go2 is not touched by tests.
- Real Qwen inference is not used in unit tests.
- Qwen model detection is read-only.
- No model files are downloaded, moved, or deleted automatically.
- Large model files are not committed to normal Git.

## Validation

- compileall passed.
- tests.test_local_qwen_provider: OK.
- tests.test_semantic_parser: OK.
- tests.test_command_flow: OK.
- tests.test_llm_fallback: OK.
- Combined focused test: 28 tests OK.
- portable check in the source project environment: PORTABLE_OK.
- release worktree portable check with the external source `.venv`: PORTABLE_WARN, expected because `.venv` is intentionally excluded from Git.
- encoding scan: DECODE_ERRORS 0, BAD_TOKENS 0.
- process check: NO_TEST_PROCESSES.

## Model Distribution

The local Whisper model `models/whisper/base.pt` was detected as larger than 100 MiB and is not part of the normal Git commit. If model delivery is required, publish the model as a GitHub Release asset or enable Git LFS intentionally.
