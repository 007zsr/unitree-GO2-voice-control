from __future__ import annotations

from pathlib import Path
from typing import Any

from src.asr.asr_env import resolve_whisper_model_dir
from src.audio.audio_diagnostics import AudioDiagnostics, analyze_audio_file
from src.models import TranscriptResult


class WhisperEngine:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._model = None
        self.model_dir = resolve_whisper_model_dir(config)

    def transcribe(self, audio_path: str | Path) -> TranscriptResult:
        target = Path(audio_path)
        min_bytes = int(self.config.get("min_audio_bytes", 512))
        silence_threshold = float(self.config.get("silence_rms_threshold", 0.01))
        diagnostics = analyze_audio_file(
            target,
            silence_rms_threshold=silence_threshold,
            min_file_bytes=min_bytes,
        )
        if not diagnostics.exists:
            return self._build_transcript(
                diagnostics,
                error_message=diagnostics.error_message,
                reason_guess="missing_audio_file",
                raw_result={"error": diagnostics.error_message},
            )
        if diagnostics.error_message:
            return self._build_transcript(
                diagnostics,
                error_message=f"ASR not executed: {diagnostics.error_message}",
                reason_guess="invalid_audio_file",
                raw_result={"error": diagnostics.error_message},
            )
        if diagnostics.duration_sec <= 0:
            return self._build_transcript(
                diagnostics,
                error_message="ASR not executed: audio file is invalid or duration is 0.",
                reason_guess="zero_duration",
                raw_result={"error": "audio duration is zero"},
            )
        if diagnostics.is_silent_like:
            return self._build_transcript(
                diagnostics,
                error_message=(
                    "ASR did not run: audio RMS is too low and looks like silence; 音量过低。"
                ),
                reason_guess="silent_audio",
                raw_result={"error": "audio is silent-like", "diagnostics": diagnostics.to_dict()},
            )

        try:
            model = self._load_model()
            kwargs = self._transcribe_kwargs()
            result = model.transcribe(str(target), **kwargs)
            text = str(result.get("text") or "").strip()
            no_speech_prob = self._extract_no_speech_prob(result)
            duration_sec = self._extract_duration(result) or diagnostics.duration_sec
            segments = self._segments(result)
            reason_guess = self._guess_empty_reason(
                text=text,
                segments=segments,
                diagnostics=diagnostics,
                no_speech_prob=no_speech_prob,
            )
            error_message = ""
            if not text:
                if reason_guess == "silent_audio":
                    error_message = (
                        "ASR did not recognize text: audio volume is too low; "
                        "the microphone may not have captured speech; 音量过低。"
                    )
                elif reason_guess == "no_speech":
                    error_message = (
                        "ASR did not recognize text: Whisper marked the segment as "
                        "likely silence or non-speech."
                    )
                elif reason_guess == "empty_segments":
                    error_message = (
                        "ASR did not recognize text: Whisper returned no text segments."
                    )
                else:
                    error_message = (
                        "ASR did not recognize text: Whisper executed but returned empty text."
                    )
            return self._build_transcript(
                diagnostics,
                text=text,
                language=str(result.get("language") or ""),
                duration_sec=duration_sec,
                no_speech_prob=no_speech_prob,
                error_message=error_message,
                whisper_loaded=True,
                whisper_executed=True,
                raw_result=result,
                segments=segments,
                reason_guess=reason_guess,
            )
        except Exception as exc:
            return self._build_transcript(
                diagnostics,
                error_message=f"ASR execution failed: {exc.__class__.__name__}: {exc}",
                reason_guess="model_failed",
                whisper_loaded=self._model is not None,
                whisper_executed=False,
                raw_result={"error": f"{exc.__class__.__name__}: {exc}"},
            )

    def _load_model(self):
        if self._model is None:
            try:
                import whisper  # type: ignore
            except ModuleNotFoundError as exc:
                raise RuntimeError("Whisper is not installed") from exc
            model_size = str(self.config.get("model_size", "base"))
            self.model_dir.mkdir(parents=True, exist_ok=True)
            allow_download = bool(self.config.get("allow_download", True))
            expected_file = self.model_dir / f"{model_size}.pt"
            if not allow_download and not expected_file.exists():
                raise RuntimeError(
                    "Whisper model file is missing in project models directory: "
                    f"{expected_file}. Run scripts/model_tools/collect_whisper_models.py "
                    "or place the model file manually."
                )
            self._model = whisper.load_model(
                model_size,
                download_root=str(self.model_dir),
            )
        return self._model

    def _transcribe_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "fp16": bool(self.config.get("fp16", False)),
            "task": str(self.config.get("task", "transcribe") or "transcribe"),
            "condition_on_previous_text": bool(
                self.config.get("condition_on_previous_text", False)
            ),
        }
        language = self._language_arg()
        if language is not None:
            kwargs["language"] = language
        if "temperature" in self.config:
            kwargs["temperature"] = float(self.config.get("temperature") or 0)
        initial_prompt = str(self.config.get("initial_prompt") or "").strip()
        if initial_prompt:
            kwargs["initial_prompt"] = initial_prompt
        return kwargs

    def _language_arg(self) -> str | None:
        language = self.config.get("language")
        if language is None:
            return None
        text = str(language).strip()
        if not text or text.lower() in {"auto", "none", "null"}:
            return None
        return text

    def _build_transcript(
        self,
        diagnostics: AudioDiagnostics,
        text: str = "",
        language: str = "",
        duration_sec: float | None = None,
        no_speech_prob: float = 1.0,
        error_message: str = "",
        whisper_loaded: bool = False,
        whisper_executed: bool = False,
        raw_result: dict[str, Any] | None = None,
        segments: list[dict[str, Any]] | None = None,
        reason_guess: str = "",
    ) -> TranscriptResult:
        raw = raw_result or {}
        segments = segments if segments is not None else self._segments(raw)
        return TranscriptResult(
            text=text,
            language=language,
            duration_sec=diagnostics.duration_sec if duration_sec is None else duration_sec,
            no_speech_prob=no_speech_prob,
            language_config=str(self.config.get("language", "auto") or "auto"),
            task=str(self.config.get("task", "transcribe") or "transcribe"),
            audio_path=diagnostics.audio_path,
            audio_file_size=diagnostics.audio_file_size,
            sample_rate=diagnostics.sample_rate,
            channels=diagnostics.channels,
            peak_amplitude=diagnostics.peak_amplitude,
            rms_amplitude=diagnostics.rms_amplitude,
            is_silent_like=diagnostics.is_silent_like,
            error_message=error_message,
            whisper_model=str(self.config.get("model_size", "base")),
            whisper_model_dir=str(self.model_dir),
            whisper_loaded=whisper_loaded,
            whisper_executed=whisper_executed,
            segments_count=len(segments),
            segments_text_preview=self._segment_preview(segments),
            raw_result_keys=list(raw.keys()) if isinstance(raw, dict) else [],
            text_empty=not bool(text),
            segments_empty=len(segments) == 0,
            reason_guess=reason_guess,
            raw_result=raw,
        )

    def _extract_no_speech_prob(self, result: dict[str, Any]) -> float:
        segments = self._segments(result)
        if not segments:
            return 1.0
        values = [
            float(segment.get("no_speech_prob", 0.0))
            for segment in segments
            if isinstance(segment, dict)
        ]
        if not values:
            return 0.0
        return max(values)

    def _extract_duration(self, result: dict[str, Any]) -> float:
        segments = self._segments(result)
        if not segments:
            return 0.0
        ends = [
            float(segment.get("end", 0.0))
            for segment in segments
            if isinstance(segment, dict)
        ]
        return max(ends) if ends else 0.0

    def _segments(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        segments = result.get("segments") if isinstance(result, dict) else []
        return [segment for segment in segments or [] if isinstance(segment, dict)]

    def _segment_preview(self, segments: list[dict[str, Any]]) -> list[str]:
        preview = []
        for segment in segments[:3]:
            text = str(segment.get("text") or "").strip()
            if text:
                preview.append(text[:120])
        return preview

    def _guess_empty_reason(
        self,
        text: str,
        segments: list[dict[str, Any]],
        diagnostics: AudioDiagnostics,
        no_speech_prob: float,
    ) -> str:
        if text:
            return ""
        if diagnostics.is_silent_like:
            return "silent_audio"
        if no_speech_prob >= float(self.config.get("no_speech_threshold", 0.6)):
            return "no_speech"
        if not segments:
            return "empty_segments"
        return "unknown"
