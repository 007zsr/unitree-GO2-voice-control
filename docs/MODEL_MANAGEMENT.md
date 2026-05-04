# Model Management

Local model files belong under `models/`.

```text
models/
  whisper/
  qwen/
```

Whisper is configured to use `models/whisper/` as its model directory. Qwen is
currently rule-based unless configuration is changed to a local or remote Qwen
backend.

Large model files are ignored by Git by default. For offline migration:

1. Copy the source tree.
2. Copy needed files under `models/`.
3. Recreate `.venv` on the target system.
4. Run `project_cli.py status` and `project_cli.py asr-check`.

Model cache tools are conservative. They can scan common user cache locations
and copy confirmed model files into `models/`, but they do not delete or move
source cache files.
