from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import asdict, dataclass
import importlib.util
from pathlib import Path
import time
from typing import Any

from src.config import project_root
from src.nlu.llm_provider_base import LLMProviderContext, LLMProviderResult
from src.nlu.semantic_engine_config import resolve_model_dir


TOKENIZER_FILES = {"tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"}
WEIGHT_SUFFIXES = {".safetensors", ".bin", ".pt", ".gguf"}


@dataclass(frozen=True)
class LocalQwenModelStatus:
    provider: str
    model_dir: str
    available: bool
    exists: bool
    is_dir: bool
    has_config: bool
    tokenizer_files: list[str]
    weight_files: list[str]
    transformers_available: bool
    torch_available: bool
    format: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_local_qwen_model(model_dir: str | Path, root: Path | None = None) -> LocalQwenModelStatus:
    resolved = find_usable_local_qwen_dir(model_dir, root or project_root())
    exists = resolved.exists()
    is_dir = resolved.is_dir()
    files = list(resolved.iterdir()) if is_dir else []
    tokenizer_files = sorted(item.name for item in files if item.is_file() and item.name in TOKENIZER_FILES)
    weight_files = sorted(item.name for item in files if item.is_file() and item.suffix in WEIGHT_SUFFIXES)
    has_config = (resolved / "config.json").exists() if is_dir else False
    transformers_available = importlib.util.find_spec("transformers") is not None
    torch_available = importlib.util.find_spec("torch") is not None
    model_format = "huggingface_transformers" if has_config else "unknown"
    if any(name.endswith(".gguf") for name in weight_files):
        model_format = "gguf_reserved"

    reason = ""
    if not exists:
        reason = "model_dir_missing"
    elif not is_dir:
        reason = "model_dir_is_not_directory"
    elif not has_config:
        reason = "missing_config_json"
    elif not tokenizer_files:
        reason = "missing_tokenizer"
    elif not weight_files:
        reason = "missing_model_weights"
    elif model_format == "gguf_reserved":
        reason = "gguf_not_implemented_in_this_provider"
    elif not transformers_available:
        reason = "missing_transformers_dependency"
    elif not torch_available:
        reason = "missing_torch_dependency"

    available = not reason
    return LocalQwenModelStatus(
        provider="local_qwen",
        model_dir=str(resolved),
        available=available,
        exists=exists,
        is_dir=is_dir,
        has_config=has_config,
        tokenizer_files=tokenizer_files,
        weight_files=weight_files,
        transformers_available=transformers_available,
        torch_available=torch_available,
        format=model_format,
        reason=reason or "ok",
    )


def find_usable_local_qwen_dir(model_dir: str | Path, root: Path | None = None) -> Path:
    resolved = resolve_model_dir(model_dir, root or project_root())
    if _has_core_qwen_files(resolved):
        return resolved
    if resolved.is_dir():
        for child in sorted(resolved.iterdir()):
            if child.is_dir() and _has_core_qwen_files(child):
                return child
    return resolved


def _has_core_qwen_files(directory: Path) -> bool:
    if not directory.is_dir() or not (directory / "config.json").exists():
        return False
    try:
        files = list(directory.iterdir())
    except OSError:
        return False
    has_tokenizer = any(item.is_file() and item.name in TOKENIZER_FILES for item in files)
    has_weights = any(item.is_file() and item.suffix in WEIGHT_SUFFIXES for item in files)
    return has_tokenizer and has_weights


class LocalQwenProvider:
    name = "local_qwen"

    def __init__(self, config: dict[str, Any], root: Path | None = None):
        self.config = config
        self.root = root or project_root()
        self.model_dir = find_usable_local_qwen_dir(str(config.get("local_llm_model_dir") or "models/qwen"), self.root)
        self._tokenizer: Any = None
        self._model: Any = None
        self._load_error: str = ""

    def status(self) -> dict[str, Any]:
        status = check_local_qwen_model(self.model_dir, self.root).to_dict()
        if self._load_error:
            status["available"] = False
            status["reason"] = "load_failed"
            status["load_error"] = self._load_error
        status["loaded"] = self._model is not None and self._tokenizer is not None
        return status

    def generate(self, context: LLMProviderContext) -> LLMProviderResult:
        started = time.monotonic()
        status = self.status()
        if not bool(status.get("available")):
            return LLMProviderResult(
                provider=self.name,
                available=False,
                latency_ms=(time.monotonic() - started) * 1000,
                error_type=str(status.get("reason") or "provider_unavailable"),
                error_message=f"Local Qwen unavailable: {status.get('reason')}",
                model_status=status,
            )
        try:
            self._ensure_loaded()
            timeout = float(self.config.get("llm_timeout_seconds", 5.0))
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(self._generate_once, context)
            try:
                raw_output = future.result(timeout=timeout)
            except FutureTimeoutError:
                future.cancel()
                executor.shutdown(wait=False, cancel_futures=True)
                return LLMProviderResult(
                    provider=self.name,
                    available=False,
                    latency_ms=(time.monotonic() - started) * 1000,
                    error_type="timeout",
                    error_message=f"Local Qwen generation timed out after {timeout:.1f}s.",
                    model_status=self.status(),
                )
            executor.shutdown(wait=False)
            return LLMProviderResult(
                provider=self.name,
                available=True,
                raw_output=raw_output,
                latency_ms=(time.monotonic() - started) * 1000,
                model_status=self.status(),
            )
        except Exception as exc:
            self._load_error = f"{exc.__class__.__name__}: {exc}"
            return LLMProviderResult(
                provider=self.name,
                available=False,
                latency_ms=(time.monotonic() - started) * 1000,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
                model_status=self.status(),
            )

    def _ensure_loaded(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

        self._tokenizer = AutoTokenizer.from_pretrained(
            str(self.model_dir),
            local_files_only=True,
            trust_remote_code=True,
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            str(self.model_dir),
            local_files_only=True,
            trust_remote_code=True,
            torch_dtype="auto",
        )
        try:
            import torch  # type: ignore

            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model.to(device)
        except Exception:
            pass
        self._model.eval()

    def _generate_once(self, context: LLMProviderContext) -> str:
        tokenizer = self._tokenizer
        model = self._model
        messages = context.prompt_messages()
        if hasattr(tokenizer, "apply_chat_template"):
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        else:
            prompt = "\n".join(f"{item['role']}: {item['content']}" for item in messages) + "\nassistant:"
        inputs = tokenizer(prompt, return_tensors="pt")
        try:
            device = next(model.parameters()).device
            inputs = {key: value.to(device) for key, value in inputs.items()}
        except Exception:
            pass
        temperature = float(self.config.get("llm_temperature", 0.0))
        max_new_tokens = int(self.config.get("llm_max_output_tokens", 128))
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0,
            temperature=max(temperature, 0.01),
            pad_token_id=getattr(tokenizer, "eos_token_id", None),
        )
        prompt_len = inputs["input_ids"].shape[-1]
        return str(tokenizer.decode(output[0][prompt_len:], skip_special_tokens=True)).strip()
