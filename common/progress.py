"""Shared progress and cancellation helpers for long-running workflows."""

from __future__ import annotations

import queue
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Callable


@dataclass(frozen=True)
class ProgressSnapshot:
    current: int = 0
    total: int = 0
    institution: str = ""
    stage: str = "Starting"
    skipped_count: int = 0


class CancellationToken:
    def __init__(self) -> None:
        self._cancel_requested = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_requested


class ProgressReporter:
    def __init__(self, callback: Callable[[ProgressSnapshot], None] | None = None) -> None:
        self._callback = callback
        self._snapshot = ProgressSnapshot()

    def update(
        self,
        *,
        current: int | None = None,
        total: int | None = None,
        institution: str | None = None,
        stage: str | None = None,
        skipped_count: int | None = None,
    ) -> None:
        self._snapshot = ProgressSnapshot(
            current=self._snapshot.current if current is None else current,
            total=self._snapshot.total if total is None else total,
            institution=self._snapshot.institution if institution is None else institution,
            stage=self._snapshot.stage if stage is None else stage,
            skipped_count=self._snapshot.skipped_count if skipped_count is None else skipped_count,
        )
        if self._callback:
            self._callback(self._snapshot)


class ProcessingDialog:
    def __init__(
        self,
        root: tk.Tk,
        title: str,
        progress_queue: "queue.Queue[ProgressSnapshot]",
        cancel_token: CancellationToken,
        *,
        allow_cancel: bool = True,
    ) -> None:
        self.root = root
        self.progress_queue = progress_queue
        self.cancel_token = cancel_token
        self.win = tk.Toplevel(root)
        self.win.title(title)
        self.win.geometry("380x170")
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        self.win.grab_set()

        self.stage_var = tk.StringVar(value="Starting...")
        self.detail_var = tk.StringVar(value="")
        self.skipped_var = tk.StringVar(value="Skipped: 0")

        ttk.Label(self.win, textvariable=self.stage_var, font=("Helvetica", 13)).pack(pady=(16, 4))
        ttk.Label(self.win, textvariable=self.detail_var, wraplength=340).pack(pady=(0, 8))
        self.progress = ttk.Progressbar(self.win, mode="determinate", maximum=1)
        self.progress.pack(fill="x", padx=24, pady=4)
        ttk.Label(self.win, textvariable=self.skipped_var).pack(pady=(4, 8))

        if allow_cancel:
            ttk.Button(self.win, text="Cancel", command=self._cancel).pack()

        self.win.protocol("WM_DELETE_WINDOW", self._cancel if allow_cancel else lambda: None)
        self._center()
        self._poll()

    def destroy(self) -> None:
        if self.win.winfo_exists():
            self.win.destroy()

    def _cancel(self) -> None:
        self.cancel_token.request_cancel()
        self.stage_var.set("Cancelling...")
        self.detail_var.set("The current file will finish before processing stops.")

    def _center(self) -> None:
        self.win.update_idletasks()
        width = self.win.winfo_width()
        height = self.win.winfo_height()
        x = (self.win.winfo_screenwidth() // 2) - (width // 2)
        y = (self.win.winfo_screenheight() // 2) - (height // 2)
        self.win.geometry(f"{width}x{height}+{x}+{y}")

    def _poll(self) -> None:
        try:
            while True:
                snapshot = self.progress_queue.get_nowait()
                self._apply(snapshot)
        except queue.Empty:
            pass

        if self.win.winfo_exists():
            self.win.after(100, self._poll)

    def _apply(self, snapshot: ProgressSnapshot) -> None:
        total = max(snapshot.total, 1)
        self.progress.configure(maximum=total)
        self.progress["value"] = min(snapshot.current, total)
        self.stage_var.set(snapshot.stage)
        if snapshot.total:
            self.detail_var.set(
                f"{snapshot.current} of {snapshot.total}"
                + (f" - {snapshot.institution}" if snapshot.institution else "")
            )
        elif snapshot.institution:
            self.detail_var.set(snapshot.institution)
        self.skipped_var.set(f"Skipped: {snapshot.skipped_count}")
