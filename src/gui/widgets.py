from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any


class LabeledText(ttk.Frame):
    def __init__(self, master: tk.Misc, title: str, height: int = 6):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.title_label = ttk.Label(self, text=title)
        self.title_label.grid(row=0, column=0, sticky="w", padx=4, pady=(4, 0))
        self.text = ScrolledText(self, height=height, wrap="word")
        self.text.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.rowconfigure(1, weight=1)

    def set_text(self, value: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
        self.text.configure(state="disabled")

    def set_title(self, value: str) -> None:
        self.title_label.configure(text=value)

    def append_line(self, value: str) -> None:
        self.text.configure(state="normal")
        self.text.insert("end", value + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    def set_json(self, value: Any) -> None:
        if value is None:
            self.set_text("")
        else:
            self.set_text(json.dumps(value, ensure_ascii=False, indent=2, default=str))
