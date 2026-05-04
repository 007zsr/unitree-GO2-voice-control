from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
from typing import Any, Callable

from src.audio.audio_capture import AudioCapture
from src.audio.audio_diagnostics import analyze_audio_file, copy_recent_audio
from src.audio.audio_env import AudioDependencyError, check_audio_dependencies
from src.audio.vad_segmenter import FixedChunkSegmenter, RollingWindowSegmenter
from src.config import ConfigSet
from src.models import PipelineDebugResult


ProcessAudio = Callable[[str | Path, str], PipelineDebugResult]
ResultCallback = Callable[[PipelineDebugResult], None]
EventCallback = Callable[[str], None]
ChunkCallback = Callable[[dict[str, Any]], None]


class OneShotVoiceWorker(threading.Thread):
    def __init__(
        self,
        configs: ConfigSet,
        process_audio: ProcessAudio,
        on_result: ResultCallback,
        on_event: EventCallback | None = None,
        on_chunk: ChunkCallback | None = None,
    ):
        super().__init__(name="go2-one-shot-voice", daemon=True)
        self.configs = configs
        self.process_audio = process_audio
        self.on_result = on_result
        self.on_event = on_event
        self.on_chunk = on_chunk

    def run(self) -> None:
        try:
            status = check_audio_dependencies()
            if not status.available:
                raise AudioDependencyError(status)
            self._event("recording")
            segmenter = self._build_fixed_segmenter(one_shot=True)
            audio_path = segmenter.record_next_segment()
            audio_path = self._copy_debug_audio(audio_path, "last_one_shot.wav")
            self._event(f"audio saved: {audio_path}")
            self._event("recognizing")
            result = self.process_audio(audio_path, "one_shot_audio")
            self.on_result(result)
        except AudioDependencyError as exc:
            self.on_result(
                PipelineDebugResult(
                    input_type="one_shot_audio",
                    command_id="",
                    accepted=False,
                    stage="audio_dependency",
                    message=exc.status.user_message(),
                    transcript_text="not executed",
                    queue_result="not_started",
                    error_stage="audio_dependency",
                    error_message=exc.status.user_message(),
                )
            )
        except Exception as exc:
            self.on_result(
                PipelineDebugResult(
                    input_type="one_shot_audio",
                    command_id="",
                    accepted=False,
                    stage="audio",
                    message=f"{exc.__class__.__name__}: {exc}",
                    error_stage="audio",
                    error_message=str(exc),
                )
            )
        finally:
            self._event("idle")

    def _build_fixed_segmenter(self, one_shot: bool) -> FixedChunkSegmenter:
        audio_config = self.configs.app.get("audio", {})
        record_sec_key = "one_shot_record_sec" if one_shot else "continuous_chunk_sec"
        chunk_sec = float(audio_config.get(record_sec_key, 3))
        temp_dir = self._resolve_project_path(str(audio_config.get("temp_dir", "runtime_data/temp_audio")))
        input_device = audio_config.get("input_device", "default")
        capture = AudioCapture(input_device=input_device)
        return FixedChunkSegmenter(capture, temp_dir=temp_dir, chunk_sec=chunk_sec)

    def _build_rolling_segmenter(self) -> RollingWindowSegmenter:
        audio_config = self.configs.app.get("audio", {})
        listening_config = self.configs.app.get("listening", {})
        temp_dir = self._resolve_project_path(str(audio_config.get("temp_dir", "runtime_data/temp_audio")))
        input_device = audio_config.get("input_device", "default")
        capture = AudioCapture(input_device=input_device)
        return RollingWindowSegmenter(
            capture,
            temp_dir=temp_dir,
            window_sec=float(listening_config.get("window_sec", 4.0)),
            hop_sec=float(listening_config.get("hop_sec", 1.5)),
        )

    def _resolve_project_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.configs.config_dir.parent / path

    def _debug_audio_dir(self) -> Path:
        audio_config = self.configs.app.get("audio", {})
        return self._resolve_project_path(str(audio_config.get("debug_dir", "runtime_data/debug_audio")))

    def _copy_debug_audio(self, source: str | Path, name: str) -> Path:
        return copy_recent_audio(source, self._debug_audio_dir() / name)

    def _event(self, message: str) -> None:
        if self.on_event:
            self.on_event(message)

    def _chunk(self, payload: dict[str, Any]) -> None:
        if self.on_chunk:
            self.on_chunk(payload)

    def _chunk_status_from_result(self, result: PipelineDebugResult) -> dict[str, Any]:
        semantic = result.semantic_result or {}
        if result.stage == "deduplicate":
            status = "duplicate_skipped"
        elif result.stage == "confirmation":
            status = "needs_confirmation"
        elif result.stage == "safety":
            status = "safety_rejected"
        elif result.error_stage:
            status = "asr_empty" if result.error_stage == "asr" else "error"
        elif semantic.get("is_command") is False:
            reason = str(semantic.get("reason") or "")
            if "ambiguous_" in reason:
                status = "ambiguous_rejected"
            elif "strict" in reason or "single_direction_word_rejected" in reason:
                status = "strict_rejected"
            else:
                status = "non_command"
        elif semantic.get("is_command") is True:
            status = "command_detected"
        elif result.transcript_text:
            status = "asr_success"
        else:
            status = "asr_empty"
        return {
            "chunk_status": status,
            "message": result.message,
            "command_id": result.command_id,
            "stage": result.stage,
            "accepted": result.accepted,
            "transcript_text": result.transcript_text,
            "error_stage": result.error_stage or "",
            "error_message": result.error_message or "",
        }


class ContinuousListeningWorker(OneShotVoiceWorker):
    def __init__(
        self,
        configs: ConfigSet,
        process_audio: ProcessAudio,
        on_result: ResultCallback,
        on_event: EventCallback | None = None,
        on_chunk: ChunkCallback | None = None,
    ):
        super().__init__(configs, process_audio, on_result, on_event, on_chunk)
        self.name = "go2-continuous-listening"
        self._stop_event = threading.Event()
        self._last_silent_notice_at = 0.0
        self._last_queue_notice_at = 0.0

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        worker: threading.Thread | None = None
        work_queue: queue.Queue[dict[str, Any]]
        try:
            status = check_audio_dependencies()
            if not status.available:
                raise AudioDependencyError(status)
            listening_config = self.configs.app.get("listening", {})
            max_queue_size = int(listening_config.get("max_queue_size", 3))
            min_rms = float(listening_config.get("min_rms", 0.01))
            work_queue = queue.Queue(maxsize=max_queue_size)
            worker = threading.Thread(
                target=self._asr_worker_loop,
                name="go2-continuous-asr-worker",
                args=(work_queue,),
                daemon=True,
            )
            worker.start()

            segmenter = self._build_continuous_segmenter()
            self._event("listening")
            while not self._stop_event.is_set():
                audio_path = segmenter.record_next_segment()
                if self._stop_event.is_set():
                    break
                audio_path = self._copy_debug_audio(audio_path, "last_listening_chunk.wav")
                diagnostics = analyze_audio_file(audio_path, silence_rms_threshold=min_rms)
                chunk_base = {
                    "audio_debug_path": str(audio_path),
                    "duration_sec": diagnostics.duration_sec,
                    "sample_rate": diagnostics.sample_rate,
                    "channels": diagnostics.channels,
                    "rms": diagnostics.rms_amplitude,
                    "peak": diagnostics.peak_amplitude,
                    "is_silent_like": diagnostics.is_silent_like,
                    "asr_diagnostics": diagnostics.to_dict(),
                }
                if diagnostics.is_silent_like:
                    self._chunk(
                        {
                            **chunk_base,
                            "chunk_status": "skipped_silent",
                            "message": "silent-like rolling window skipped",
                        }
                    )
                    self._rate_limited_silent_notice(diagnostics.rms_amplitude, diagnostics.peak_amplitude)
                    continue
                self._enqueue_window(work_queue, {"audio_path": audio_path, "chunk_base": chunk_base})
        except AudioDependencyError as exc:
            self.on_result(
                PipelineDebugResult(
                    input_type="continuous_audio",
                    command_id="",
                    accepted=False,
                    stage="audio_dependency",
                    message=exc.status.user_message(),
                    transcript_text="not executed",
                    queue_result="not_started",
                    error_stage="audio_dependency",
                    error_message=exc.status.user_message(),
                )
            )
        except Exception as exc:
            self.on_result(
                PipelineDebugResult(
                    input_type="continuous_audio",
                    command_id="",
                    accepted=False,
                    stage="listening",
                    message=f"{exc.__class__.__name__}: {exc}",
                    error_stage="listening",
                    error_message=str(exc),
                )
            )
        finally:
            self._stop_event.set()
            if worker:
                worker.join(timeout=5)
            self._event("idle")

    def _build_continuous_segmenter(self):
        listening_config = self.configs.app.get("listening", {})
        if str(listening_config.get("mode", "rolling_window")) == "rolling_window":
            return self._build_rolling_segmenter()
        return self._build_fixed_segmenter(one_shot=False)

    def _enqueue_window(
        self,
        work_queue: queue.Queue[dict[str, Any]],
        payload: dict[str, Any],
    ) -> None:
        if work_queue.full():
            try:
                dropped = work_queue.get_nowait()
                self._chunk(
                    {
                        **dropped.get("chunk_base", {}),
                        "chunk_status": "dropped_queue_full",
                        "message": "ASR queue was full; oldest window dropped",
                    }
                )
            except queue.Empty:
                pass
            self._rate_limited_queue_notice()
        work_queue.put(payload)
        self._event("listening")

    def _asr_worker_loop(self, work_queue: queue.Queue[dict[str, Any]]) -> None:
        while not self._stop_event.is_set() or not work_queue.empty():
            try:
                item = work_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            audio_path = item["audio_path"]
            chunk_base = item.get("chunk_base", {})
            try:
                self._event("processing")
                result = self.process_audio(audio_path, "continuous_audio")
                self._chunk({**chunk_base, **self._chunk_status_from_result(result)})
                self.on_result(result)
            finally:
                work_queue.task_done()
                if not self._stop_event.is_set():
                    self._event("listening")

    def _rate_limited_silent_notice(self, rms: float, peak: float) -> None:
        now = time.monotonic()
        if now - self._last_silent_notice_at >= 10.0:
            self._event(f"skipped silent window (RMS={rms:.4f}, peak={peak:.4f})")
            self._last_silent_notice_at = now

    def _rate_limited_queue_notice(self) -> None:
        now = time.monotonic()
        if now - self._last_queue_notice_at >= 5.0:
            self._event("ASR queue is full; dropping the oldest rolling window")
            self._last_queue_notice_at = now
