from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from src.gui.i18n import I18n


class SettingsWindow(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        settings: dict[str, object],
        i18n: I18n,
        on_save: Callable[[dict[str, object]], None],
        on_check_model: Callable[[], dict[str, object]] | None = None,
    ):
        super().__init__(master)
        self.i18n = i18n
        self.on_save = on_save
        self.on_check_model = on_check_model
        self.title(i18n.t("settings.title"))
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.ui_language = tk.StringVar(value=str(settings.get("ui_language", "en")))
        self.recognition_preference = tk.StringVar(
            value=str(settings.get("recognition_preference", "auto"))
        )
        self.command_detection_mode = tk.StringVar(
            value=str(settings.get("command_detection_mode", "strict"))
        )
        self.deduplicate_enabled = tk.BooleanVar(
            value=bool(settings.get("deduplicate_enabled", True))
        )
        self.deduplicate_window_sec = tk.StringVar(
            value=str(settings.get("deduplicate_window_sec", 3.0))
        )
        self.same_intent_cooldown_sec = tk.StringVar(
            value=str(settings.get("same_intent_cooldown_sec", 2.5))
        )
        self.semantic_engine_mode = tk.StringVar(value=str(settings.get("semantic_engine_mode", "traditional")))
        self.llm_enabled = tk.BooleanVar(value=bool(settings.get("llm_enabled", False)))
        self.llm_provider = tk.StringVar(value=str(settings.get("llm_provider", "local_qwen")))
        self.llm_fallback_min_confidence = tk.StringVar(
            value=str(settings.get("llm_fallback_min_confidence", 0.60))
        )
        self.local_llm_model_dir = tk.StringVar(value=str(settings.get("local_llm_model_dir", "models/qwen")))
        self.llm_timeout_seconds = tk.StringVar(value=str(settings.get("llm_timeout_seconds", 5.0)))
        self.llm_max_output_tokens = tk.StringVar(value=str(settings.get("llm_max_output_tokens", 128)))
        self.llm_temperature = tk.StringVar(value=str(settings.get("llm_temperature", 0.0)))
        self.llm_allow_remote_api = tk.BooleanVar(value=bool(settings.get("llm_allow_remote_api", False)))

        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")

        self._row(
            frame,
            0,
            self.i18n.t("settings.ui_language"),
            ttk.Combobox(frame, textvariable=self.ui_language, values=["en", "zh"], state="readonly", width=24),
        )
        self._row(
            frame,
            1,
            self.i18n.t("settings.recognition"),
            ttk.Combobox(
                frame,
                textvariable=self.recognition_preference,
                values=["auto", "english_preferred", "chinese_preferred"],
                state="readonly",
                width=24,
            ),
        )
        self._row(
            frame,
            2,
            self.i18n.t("settings.command_mode"),
            ttk.Combobox(
                frame,
                textvariable=self.command_detection_mode,
                values=["strict", "relaxed"],
                state="readonly",
                width=24,
            ),
        )
        ttk.Checkbutton(
            frame,
            text=self.i18n.t("settings.dedup"),
            variable=self.deduplicate_enabled,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=4)
        self._row(
            frame,
            4,
            self.i18n.t("settings.dedup_window"),
            ttk.Entry(frame, textvariable=self.deduplicate_window_sec, width=26),
        )
        self._row(
            frame,
            5,
            self.i18n.t("settings.cooldown"),
            ttk.Entry(frame, textvariable=self.same_intent_cooldown_sec, width=26),
        )
        ttk.Separator(frame, orient="horizontal").grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 8))
        self._row(
            frame,
            7,
            self.i18n.t("settings.semantic_mode"),
            ttk.Combobox(
                frame,
                textvariable=self.semantic_engine_mode,
                values=["traditional", "llm_fallback", "llm_only_debug"],
                state="readonly",
                width=24,
            ),
        )
        ttk.Checkbutton(
            frame,
            text=self.i18n.t("settings.llm_enabled"),
            variable=self.llm_enabled,
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=4)
        self._row(
            frame,
            9,
            self.i18n.t("settings.llm_provider"),
            ttk.Combobox(
                frame,
                textvariable=self.llm_provider,
                values=["local_qwen", "disabled", "mock", "openai_api_reserved", "custom_api_reserved"],
                state="readonly",
                width=24,
            ),
        )
        self._row(
            frame,
            10,
            self.i18n.t("settings.local_model_dir"),
            ttk.Entry(frame, textvariable=self.local_llm_model_dir, width=26),
        )
        self._row(
            frame,
            11,
            self.i18n.t("settings.llm_min_conf"),
            ttk.Entry(frame, textvariable=self.llm_fallback_min_confidence, width=26),
        )
        self._row(
            frame,
            12,
            self.i18n.t("settings.llm_timeout"),
            ttk.Entry(frame, textvariable=self.llm_timeout_seconds, width=26),
        )
        self._row(
            frame,
            13,
            self.i18n.t("settings.llm_tokens"),
            ttk.Entry(frame, textvariable=self.llm_max_output_tokens, width=26),
        )
        self._row(
            frame,
            14,
            self.i18n.t("settings.llm_temperature"),
            ttk.Entry(frame, textvariable=self.llm_temperature, width=26),
        )
        ttk.Checkbutton(
            frame,
            text=self.i18n.t("settings.allow_remote_api"),
            variable=self.llm_allow_remote_api,
        ).grid(row=15, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Label(
            frame,
            text=self.i18n.t("settings.llm_safety_note"),
            wraplength=420,
        ).grid(row=16, column=0, columnspan=2, sticky="w", pady=(6, 2))
        ttk.Button(
            frame,
            text=self.i18n.t("settings.check_model"),
            command=self._check_model,
        ).grid(row=17, column=0, columnspan=2, sticky="w", pady=(4, 0))

        buttons = ttk.Frame(frame)
        buttons.grid(row=18, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text=self.i18n.t("settings.cancel"), command=self.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(buttons, text=self.i18n.t("settings.save"), command=self._save).grid(row=0, column=1, padx=4)

    def _row(self, frame: ttk.Frame, row: int, label: str, widget: ttk.Widget) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 12))
        widget.grid(row=row, column=1, sticky="ew", pady=4)

    def _save(self) -> None:
        self.on_save(
            {
                "ui_language": self.ui_language.get(),
                "recognition_preference": self.recognition_preference.get(),
                "command_detection_mode": self.command_detection_mode.get(),
                "deduplicate_enabled": self.deduplicate_enabled.get(),
                "deduplicate_window_sec": float(self.deduplicate_window_sec.get() or 3.0),
                "same_intent_cooldown_sec": float(self.same_intent_cooldown_sec.get() or 2.5),
                "semantic_engine_mode": self.semantic_engine_mode.get(),
                "llm_enabled": self.llm_enabled.get(),
                "llm_provider": self.llm_provider.get(),
                "llm_fallback_min_confidence": float(self.llm_fallback_min_confidence.get() or 0.60),
                "local_llm_model_dir": self.local_llm_model_dir.get(),
                "llm_timeout_seconds": float(self.llm_timeout_seconds.get() or 5.0),
                "llm_max_output_tokens": int(float(self.llm_max_output_tokens.get() or 128)),
                "llm_temperature": float(self.llm_temperature.get() or 0.0),
                "llm_allow_remote_api": self.llm_allow_remote_api.get(),
            }
        )
        self.destroy()

    def _check_model(self) -> None:
        if self.on_check_model is None:
            return
        status = self.on_check_model()
        available = bool(status.get("available"))
        reason = str(status.get("reason") or "")
        model_dir = str(status.get("model_dir") or "")
        message = (
            f"available={available}\n"
            f"reason={reason}\n"
            f"model_dir={model_dir}\n"
            f"tokenizer={', '.join(str(x) for x in status.get('tokenizer_files', []) or []) or '-'}\n"
            f"weights={', '.join(str(x) for x in status.get('weight_files', []) or []) or '-'}"
        )
        messagebox.showinfo(self.i18n.t("settings.check_model"), message, parent=self)
