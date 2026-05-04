# Changelog

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
