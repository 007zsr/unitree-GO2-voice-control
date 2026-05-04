from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from src.gui.i18n import I18n


class SettingsWindow(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        settings: dict[str, object],
        i18n: I18n,
        on_save: Callable[[dict[str, object]], None],
    ):
        super().__init__(master)
        self.i18n = i18n
        self.on_save = on_save
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

        buttons = ttk.Frame(frame)
        buttons.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))
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
            }
        )
        self.destroy()
