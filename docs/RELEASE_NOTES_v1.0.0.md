# Release Notes - v1.0.0

This is the first organized release of the Unitree Go2 voice control prototype.

## Current Status

The following pipeline is implemented:

```text
GUI -> Whisper ASR -> NLU -> CommandPlan -> Safety -> CommandQueue -> MockAdapter
```

## Main Features

- GUI interface
- One-shot text command
- One-shot voice command
- Continuous listening
- Whisper speech recognition
- Chinese / English / mixed-language command recognition
- Sequential command planning
- Fuzzy command recognition
- Safety checks
- Mock execution
- Structured logs
- Batch text testing

## Important Safety Note

This version does not enable real Go2 robot movement by default.

Default configuration:

```yaml
robot_mode: mock
enable_real_robot: false
```

## Known Limitations

- Real Go2 hardware has not been validated.
- Qwen local model is not fully enabled.
- Whisper may still misrecognize some speech.
- Ubuntu / anbangtu deployment still needs validation.
