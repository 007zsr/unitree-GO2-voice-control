# Local Models

This directory is reserved for local model files used by the project.

Whisper model weights should be stored under:

```text
models/whisper/
```

Local Qwen model directories, when used by the optional LLM fallback semantic
engine, should be stored under:

```text
models/qwen/
```

Large model files are intentionally ignored by Git. Keep source code,
configuration, and setup scripts in the repository; recreate Python
dependencies with `.venv` and `requirements-*.txt`, and copy model files
separately when preparing an offline Ubuntu/anbangtu deployment.

For public distribution, attach model files to a GitHub Release or enable Git
LFS intentionally. Do not commit Whisper `.pt` files, Qwen `.bin` files,
`.safetensors`, or `.gguf` files to normal Git history.
