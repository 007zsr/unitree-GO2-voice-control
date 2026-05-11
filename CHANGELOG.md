# Changelog

## V1.1 - Qwen / LLM fallback semantic engine

### Added

- Added semantic engine configuration for traditional mode, LLM fallback mode, and LLM debug mode.
- Added LLM provider base layer with LLMRequest, LLMResponse, and provider error types.
- Added MockLLMProvider for safe tests and fallback validation.
- Added LocalQwenProvider availability checks with lazy-loading safety.
- Added compatibility aliases for legacy config names.
- Added fallback tests for semantic parser, command flow, and provider routing.

### Changed

- Invalid semantic engine mode now safely falls back to traditional mode.
- LLM is disabled automatically when semantic mode is invalid.
- Provider name `mock_llm` is normalized to `mock`.
- Logging redaction now includes password-like keys.

### Safety

- LLM fallback does not bypass CommandPlan.
- LLM fallback does not bypass SafetyController.
- LLM fallback does not call Adapter directly.
- Real Qwen inference is not used in unit tests.
- Real Go2 is not touched by this release.
- Large model files remain outside normal Git commits.

### Validation

- compileall passed.
- `tests.test_local_qwen_provider` passed.
- `tests.test_semantic_parser` passed.
- `tests.test_command_flow` passed.
- `tests.test_llm_fallback` passed.
- Small combined test: 28 tests OK.
- portable check in the source project environment: PORTABLE_OK.
- release worktree portable check with the external source `.venv`: PORTABLE_WARN, expected because `.venv` is intentionally excluded from Git.
- encoding scan: DECODE_ERRORS 0, BAD_TOKENS 0.
- process check: NO_TEST_PROCESSES.

## v1.0.0 - Initial public release

### Added

- GUI control panel for Unitree Go2 voice control prototype.
- One-shot text command mode.
- One-shot voice command mode.
- Continuous listening mode.
- Whisper-based speech recognition pipeline.
- Rule-based NLU with Chinese, English, and mixed-language command support.
- CommandPlan for sequential commands.
- Fuzzy command recognition.
- SafetyController for command validation.
- CommandQueue with emergency stop priority.
- MockAdapter for safe simulated execution.
- Go2Adapter framework for future real robot integration.
- Structured logging system.
- Batch fuzzy text test system.
- Project-local Whisper model directory support.

### Notes

- Real Go2 robot execution is disabled by default.
- The current release is Mock-first.
- Qwen local model is reserved but not fully enabled.
- Ubuntu / anbangtu deployment still requires validation.
