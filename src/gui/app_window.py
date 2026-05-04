from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from src.gui.gui_runtime_bridge import GuiRuntimeBridge
from src.gui.i18n import I18n
from src.gui.settings_window import SettingsWindow
from src.gui.widgets import LabeledText
from src.models import PipelineDebugResult


class Go2VoiceControlWindow(tk.Tk):
    def __init__(self, config_dir: str | Path | None = None):
        super().__init__()
        self.bridge = GuiRuntimeBridge(config_dir)
        self.i18n = I18n(str(self.bridge.get_settings().get("ui_language", "en")))
        self.title(self.i18n.t("app.title"))
        self.geometry("1180x880")
        self.minsize(980, 720)
        self.ui_queue: queue.Queue[tuple[str, object]] = queue.Queue()

        self.listening_state = tk.StringVar(value="Listening: idle")
        self.mode_state = tk.StringVar(value="Mode: loading")
        self.semantic_state = tk.StringVar(value="NLU: loading")
        self.asr_state = tk.StringVar(value="ASR: loading")
        self.asr_dependency_state = tk.StringVar(value="ASR status: checking")
        self.audio_state = tk.StringVar(value="Audio status: checking")
        self.settings_state = tk.StringVar(value="Settings: loading")
        self.log_paths_state = tk.StringVar(value="Logs: loading")
        self.text_input = tk.StringVar(value="stand up please")
        self.command_filter = tk.StringVar(value="All")

        self._configure_style()
        self._build_layout()
        self._apply_i18n()
        self._start_runtime()
        self.after(100, self._drain_ui_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Warning.TLabel", foreground="#b00020", font=("TkDefaultFont", 10, "bold"))
        style.configure("Status.TLabel", font=("TkDefaultFont", 10, "bold"))

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        status = ttk.Frame(self, padding=8)
        status.grid(row=0, column=0, sticky="ew")
        for index in range(6):
            status.columnconfigure(index, weight=1)
        ttk.Label(status, textvariable=self.mode_state, style="Status.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(status, textvariable=self.listening_state, style="Status.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(status, textvariable=self.semantic_state, style="Status.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Label(status, textvariable=self.asr_state, style="Status.TLabel").grid(row=0, column=3, sticky="w")
        ttk.Label(status, textvariable=self.asr_dependency_state, style="Status.TLabel").grid(row=0, column=4, sticky="w")
        ttk.Label(status, textvariable=self.audio_state, style="Status.TLabel").grid(row=0, column=5, sticky="w")
        ttk.Label(status, textvariable=self.settings_state, style="Status.TLabel").grid(
            row=1,
            column=0,
            columnspan=6,
            sticky="w",
            pady=(4, 0),
        )

        controls = ttk.Frame(self, padding=(8, 0, 8, 8))
        controls.grid(row=1, column=0, sticky="ew")
        controls.columnconfigure(0, weight=1)
        ttk.Entry(controls, textvariable=self.text_input).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.start_listen_button = ttk.Button(controls, command=self._start_listening)
        self.start_listen_button.grid(row=0, column=1, padx=3)
        self.stop_listen_button = ttk.Button(controls, command=self._stop_listening)
        self.stop_listen_button.grid(row=0, column=2, padx=3)
        self.one_shot_voice_button = ttk.Button(controls, command=self._process_one_shot_voice)
        self.one_shot_voice_button.grid(row=0, column=3, padx=3)
        self.one_shot_text_button = ttk.Button(controls, command=self._process_text)
        self.one_shot_text_button.grid(row=0, column=4, padx=3)
        self.emergency_button = ttk.Button(controls, command=self._emergency_stop)
        self.emergency_button.grid(row=0, column=5, padx=3)
        self.settings_button = ttk.Button(controls, command=self._open_settings)
        self.settings_button.grid(row=0, column=6, padx=3)
        self.clear_log_button = ttk.Button(controls, command=self._clear_log)
        self.clear_log_button.grid(row=0, column=7, padx=(3, 0))
        self.command_filter_combo = ttk.Combobox(
            controls,
            textvariable=self.command_filter,
            values=["All", "Safe", "Caution", "Dangerous", "Disabled"],
            state="readonly",
            width=12,
        )
        self.command_filter_combo.grid(row=0, column=8, padx=(6, 0))
        self.command_filter_combo.bind("<<ComboboxSelected>>", lambda _event: self._refresh_command_list())

        self.warning_label = ttk.Label(self, text="", style="Warning.TLabel", padding=(8, 0, 8, 8))
        self.warning_label.grid(row=2, column=0, sticky="ew")

        self.log_paths_label = ttk.Label(self, textvariable=self.log_paths_state, padding=(8, 0, 8, 8))
        self.log_paths_label.grid(row=3, column=0, sticky="ew")

        panes = ttk.PanedWindow(self, orient="horizontal")
        panes.grid(row=4, column=0, sticky="nsew", padx=8, pady=(0, 8))

        left = ttk.Frame(panes)
        right = ttk.Frame(panes)
        panes.add(left, weight=1)
        panes.add(right, weight=1)
        for frame in [left, right]:
            frame.columnconfigure(0, weight=1)
            for index in range(5):
                frame.rowconfigure(index, weight=1)

        self.asr_panel = LabeledText(left, "ASR transcript", height=5)
        self.semantic_panel = LabeledText(left, "Semantic result", height=8)
        self.plan_panel = LabeledText(left, "Command Plan", height=7)
        self.command_panel = LabeledText(left, "RobotCommand", height=8)
        self.safety_panel = LabeledText(left, "Safety decision", height=6)
        self.asr_panel.grid(row=0, column=0, sticky="nsew")
        self.semantic_panel.grid(row=1, column=0, sticky="nsew")
        self.plan_panel.grid(row=2, column=0, sticky="nsew")
        self.command_panel.grid(row=3, column=0, sticky="nsew")
        self.safety_panel.grid(row=4, column=0, sticky="nsew")

        self.execution_panel = LabeledText(right, "Execution result", height=7)
        self.asr_debug_panel = LabeledText(right, "ASR diagnostics", height=7)
        self.debug_panel = LabeledText(right, "PipelineDebugResult", height=8)
        self.commands_panel = LabeledText(right, "Supported commands", height=6)
        self.log_panel = LabeledText(right, "UI log", height=10)
        self.execution_panel.grid(row=0, column=0, sticky="nsew")
        self.asr_debug_panel.grid(row=1, column=0, sticky="nsew")
        self.debug_panel.grid(row=2, column=0, sticky="nsew")
        self.commands_panel.grid(row=3, column=0, sticky="nsew")
        self.log_panel.grid(row=4, column=0, sticky="nsew")

    def _apply_i18n(self) -> None:
        self.title(self.i18n.t("app.title"))
        self.start_listen_button.configure(text=self.i18n.t("button.start_listening"))
        self.stop_listen_button.configure(text=self.i18n.t("button.stop_listening"))
        self.one_shot_voice_button.configure(text=self.i18n.t("button.one_shot_voice"))
        self.one_shot_text_button.configure(text=self.i18n.t("button.one_shot_text"))
        self.emergency_button.configure(text=self.i18n.t("button.emergency_stop"))
        self.settings_button.configure(text=self.i18n.t("button.settings"))
        self.clear_log_button.configure(text=self.i18n.t("button.clear_log"))
        self.asr_panel.set_title(self.i18n.t("label.asr"))
        self.semantic_panel.set_title(self.i18n.t("label.semantic"))
        self.plan_panel.set_title(self.i18n.t("label.command_plan"))
        self.command_panel.set_title(self.i18n.t("label.command"))
        self.safety_panel.set_title(self.i18n.t("label.safety"))
        self.execution_panel.set_title(self.i18n.t("label.execution"))
        self.asr_debug_panel.set_title(self.i18n.t("label.asr_debug"))
        self.debug_panel.set_title(self.i18n.t("label.debug"))
        self.commands_panel.set_title(self.i18n.t("label.commands"))
        self.log_panel.set_title(self.i18n.t("label.log"))
        self._refresh_command_list()

    def _start_runtime(self) -> None:
        try:
            self.bridge.start()
            self._refresh_status()
            self._log("Program started")
            asr_status = self.bridge.get_asr_status()
            self._log_asr_environment(asr_status.to_dict(), asr_status.environment_message())
            status = self.bridge.get_current_status()
            self._log(f"Qwen mode: {status.get('qwen_mode', 'rule_based')}")
            self._log(f"Qwen model dir: {status.get('qwen_model_dir', 'models/qwen')}")
            self._log(f"Portable status: {status.get('portable_status', 'WARN')}")
            self._log("Model cache note: the program never deletes source cache files.")
            self._log_current_paths()
            if not asr_status.available:
                self._log_asr_dependency_hint(asr_status.user_message())
        except Exception as exc:
            self._log(f"Startup failed: {exc}")
            messagebox.showerror("Startup failed", str(exc))

    def _refresh_status(self) -> None:
        status = self.bridge.get_current_status()
        settings = self.bridge.get_settings()
        robot_mode = str(status.get("robot_mode", "mock"))
        real_robot = bool(status.get("enable_real_robot"))
        adapter = status.get("adapter", "unknown")
        if robot_mode == "go2" and real_robot:
            mode_text = f"Mode: Go2 real robot ({adapter})"
            self.warning_label.configure(text="WARNING: real Go2 mode may control the physical robot.")
        else:
            mode_text = f"Mode: Mock, no real Go2 control ({adapter})"
            self.warning_label.configure(text="")
        self.mode_state.set(mode_text)
        self.semantic_state.set(f"NLU: {status.get('qwen_provider', 'unknown')}")
        self.asr_state.set(f"ASR: {status.get('asr_provider', 'unknown')}")
        self._apply_audio_status(status.get("audio", {}))
        self._apply_asr_status(status.get("asr", {}))
        audio_state = str(status.get("audio_state", "idle"))
        self._apply_voice_button_availability(status.get("audio", {}), status.get("asr", {}), audio_state)
        self._apply_workflow_state(audio_state)
        if status.get("listening"):
            listening = "listening"
        elif audio_state == "one_shot_recording":
            listening = "recording"
        elif audio_state == "processing":
            listening = "processing"
        else:
            listening = "idle"
        self.listening_state.set(f"Listening: {self.i18n.t('state.' + listening)}")
        self.settings_state.set(
            " | ".join(
                [
                    f"UI: {settings.get('ui_language')}",
                    f"Recognition: {settings.get('recognition_preference')}",
                    f"Command mode: {settings.get('command_detection_mode')}",
                    f"Dedup: {'on' if settings.get('deduplicate_enabled') else 'off'}, "
                    f"{settings.get('deduplicate_window_sec')}s",
                ]
            )
        )
        self._set_log_paths(status.get("logs", {}))

    def _apply_audio_status(self, audio_status: object) -> None:
        if not isinstance(audio_status, dict):
            return
        available = bool(audio_status.get("available"))
        missing = audio_status.get("missing_packages") or []
        if available:
            self.audio_state.set("Audio: available")
            return
        missing_text = ", ".join(str(item) for item in missing) or "sounddevice, soundfile"
        self.audio_state.set(f"Audio: unavailable, missing {missing_text}")
        self.start_listen_button.state(["disabled"])
        self.one_shot_voice_button.state(["disabled"])

    def _apply_asr_status(self, asr_status: object) -> None:
        if not isinstance(asr_status, dict):
            return
        available = bool(asr_status.get("available"))
        model_name = str(asr_status.get("model_name") or "not configured")
        if available:
            self.asr_dependency_state.set(f"ASR status: available, Whisper {model_name}")
            return
        missing = asr_status.get("missing") or []
        missing_text = ", ".join(str(item) for item in missing) or "openai-whisper / ffmpeg"
        self.asr_dependency_state.set(f"ASR status: unavailable, missing {missing_text}")
        self.start_listen_button.state(["disabled"])
        self.one_shot_voice_button.state(["disabled"])

    def _apply_voice_button_availability(self, audio_status: object, asr_status: object, audio_state: str) -> None:
        audio_available = isinstance(audio_status, dict) and bool(audio_status.get("available"))
        asr_available = isinstance(asr_status, dict) and bool(asr_status.get("available"))
        if audio_available and asr_available and audio_state == "idle":
            self.start_listen_button.state(["!disabled"])
            self.one_shot_voice_button.state(["!disabled"])
        else:
            self.start_listen_button.state(["disabled"])
            self.one_shot_voice_button.state(["disabled"])

    def _apply_workflow_state(self, audio_state: str) -> None:
        if audio_state in {"continuous_listening", "one_shot_recording", "processing"}:
            self.start_listen_button.state(["disabled"])
            self.one_shot_voice_button.state(["disabled"])

    def _process_text(self) -> None:
        text = self.text_input.get().strip()
        if not text:
            messagebox.showwarning("Empty input", "Please enter one text command.")
            return
        self._log("Button: one-shot text")
        self._run_background("text", lambda: self.bridge.process_text_once(text))

    def _process_one_shot_voice(self) -> None:
        self._log("Button: one-shot voice")
        started = self.bridge.start_one_shot_voice(
            on_result=lambda result: self.ui_queue.put(("result", result)),
            on_event=lambda event: self.ui_queue.put(("event", event)),
        )
        if not started:
            self._refresh_status()

    def _start_listening(self) -> None:
        self._log("Button: start listening")
        started = self.bridge.start_continuous_listening(
            on_result=lambda result: self.ui_queue.put(("result", result)),
            on_event=lambda event: self.ui_queue.put(("event", event)),
        )
        if started:
            self._log("Continuous listening started")
            self.listening_state.set(f"Listening: {self.i18n.t('state.listening')}")
            self._refresh_status()
        else:
            if self.bridge.get_audio_status().available and self.bridge.get_asr_status().available:
                self._log("Listening is already running")

    def _stop_listening(self) -> None:
        self._log("Button: stop listening")
        self.bridge.stop_continuous_listening()
        self.listening_state.set(f"Listening: {self.i18n.t('state.idle')}")
        self._log("Continuous listening stopped")
        self._refresh_status()

    def _emergency_stop(self) -> None:
        self._log("Button: emergency stop")
        self._run_background("emergency_stop", self.bridge.submit_emergency_stop)

    def _open_settings(self) -> None:
        self._log("Button: settings")
        SettingsWindow(self, self.bridge.get_settings(), self.i18n, self._save_settings)

    def _save_settings(self, settings: dict[str, object]) -> None:
        self.bridge.save_user_settings(settings)
        self.i18n.set_language(str(settings.get("ui_language", "en")))
        self._apply_i18n()
        self._refresh_status()
        self._log("Settings saved")

    def _refresh_command_list(self) -> None:
        language = self.i18n.language
        self.commands_panel.set_text(self.bridge.supported_commands_text(language, self.command_filter.get()))

    def _run_background(self, name: str, target) -> None:
        def runner() -> None:
            self.ui_queue.put(("event", "processing"))
            try:
                result = target()
                self.ui_queue.put(("result", result))
            finally:
                self.ui_queue.put(("event", "idle"))

        threading.Thread(target=runner, name=f"go2-gui-{name}", daemon=True).start()

    def _drain_ui_queue(self) -> None:
        while True:
            try:
                kind, payload = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "result":
                self._display_result(payload)
            elif kind == "event":
                self._handle_event(str(payload))
        self.after(100, self._drain_ui_queue)

    def _handle_event(self, event: str) -> None:
        self.listening_state.set(f"Listening: {event}")
        self._log(event)
        self._refresh_status()

    def _display_result(self, result: PipelineDebugResult) -> None:
        if result.transcript_text:
            self.asr_panel.set_text(result.transcript_text)
        elif result.asr_diagnostics and result.asr_diagnostics.get("error_message"):
            self.asr_panel.set_text(str(result.asr_diagnostics.get("error_message")))
        elif result.error_stage in {"audio_dependency", "audio_busy"}:
            self.asr_panel.set_text(result.transcript_text or "not executed")
        else:
            self.asr_panel.set_text("No text recognized")
        self.asr_debug_panel.set_json(result.asr_diagnostics)
        self.semantic_panel.set_json(result.semantic_result)
        self.plan_panel.set_json(result.command_plan)
        self.command_panel.set_json(result.robot_command)
        self.safety_panel.set_json(result.safety_decision)
        execution = {
            "accepted": result.accepted,
            "stage": result.stage,
            "message": result.message,
            "result_type": self._result_type(result),
            "queue_result": result.queue_result,
            "adapter_result": result.adapter_result,
            "error_stage": result.error_stage,
            "error_message": result.error_message,
        }
        self.execution_panel.set_json(execution)
        self.debug_panel.set_json(result.to_dict())
        semantic = result.semantic_result or {}
        if result.stage == "deduplicate":
            self._log(f"{result.command_id}: skipped duplicate command")
        elif result.stage == "confirmation":
            self._log(f"{result.command_id}: needs confirmation: {result.message}")
        elif result.stage == "safety":
            self._log(f"{result.command_id}: Safety rejected: {result.message}")
        elif semantic.get("is_command") is False:
            self._log(f"{result.command_id}: non-command, not queued")
        elif result.accepted:
            self._log(f"{result.command_id}: accepted, {result.queue_result}")
        elif result.error_stage == "audio_dependency":
            self._log_audio_dependency_hint(result)
        elif result.error_stage == "asr_dependency":
            self._log_asr_dependency_hint(result.message)
        elif result.error_stage == "audio_busy":
            self._log(result.message)
        elif result.stage == "asr":
            self._log(f"{result.command_id}: ASR failed: {result.message}")
        else:
            self._log(f"{result.command_id}: rejected at {result.stage}: {result.message}")
        self._refresh_status()

    def _result_type(self, result: PipelineDebugResult) -> str:
        if result.accepted:
            return "accepted"
        if result.stage == "safety":
            return "safety_rejected"
        if result.stage == "confirmation":
            return "needs_confirmation"
        if result.semantic_result and result.semantic_result.get("is_command") is False:
            reason = str(result.semantic_result.get("reason") or "")
            if "ambiguous_" in reason:
                return "ambiguous_rejected"
            if "strict" in reason or "single_direction_word_rejected" in reason:
                return "strict_rejected"
            return "non_command"
        if result.error_stage:
            return "system_error"
        return "rejected"

    def _log_audio_dependency_hint(self, result: PipelineDebugResult) -> None:
        self._log("Audio capture dependency missing.")
        first_line = result.message.splitlines()[0] if result.message else ""
        if first_line:
            self._log(first_line)
        self._log("Install: python -m pip install sounddevice soundfile")
        self._log("Ubuntu system packages: sudo apt install portaudio19-dev libsndfile1")

    def _log_asr_dependency_hint(self, message: str) -> None:
        self._log("ASR dependency is incomplete.")
        for line in message.splitlines():
            clean = line.strip()
            if clean:
                self._log(clean)

    def _log_asr_environment(self, asr_status: object, message: str) -> None:
        for line in message.splitlines():
            clean = line.strip()
            if clean:
                self._log(clean)
        if isinstance(asr_status, dict) and not bool(asr_status.get("is_project_venv")):
            self.warning_label.configure(
                text="WARNING: current Python is not the project .venv. Use run_gui_windows.bat or run_gui_ubuntu.sh."
            )

    def _clear_log(self) -> None:
        self._log("Button: clear UI log")
        self.log_panel.set_text("")

    def _log(self, message: str) -> None:
        self.log_panel.append_line(f"[{time.strftime('%H:%M:%S')}] {message}")
        try:
            self.bridge.log_gui_event(message)
        except Exception:
            pass

    def _log_current_paths(self) -> None:
        paths = self.bridge.get_current_log_paths()
        for key, value in paths.items():
            if value:
                self._log(f"{key}: {value}")
        self._set_log_paths(paths)

    def _set_log_paths(self, paths: object) -> None:
        if not isinstance(paths, dict):
            return
        self.log_paths_state.set(
            " | ".join(
                [
                    f"session: {paths.get('session_id', '')}",
                    f"session log: {paths.get('session_log', '')}",
                    f"task: {paths.get('current_task_log', '')}",
                    f"continuous: {paths.get('current_continuous_log', '')}",
                ]
            )
        )

    def _on_close(self) -> None:
        try:
            self._log("GUI closing")
            self.bridge.shutdown()
        finally:
            self.destroy()
