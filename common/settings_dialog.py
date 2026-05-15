"""Tkinter settings dialog for app preferences."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from . import settings
from .sports import DEFAULT_SPORT_ALIASES


def parse_alias_text(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def format_aliases(values: list[str]) -> str:
    return ", ".join(values)


def open_settings_dialog(parent):
    current_settings = settings.load_settings()
    custom_aliases = current_settings.get("custom_sport_aliases", {})

    win = tk.Toplevel(parent)
    win.title("Settings")
    win.geometry("620x520")
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    root_frame = ttk.Frame(win, padding=14)
    root_frame.pack(fill="both", expand=True)

    ttk.Label(root_frame, text="Sport Alias Settings", font=("Segoe UI", 14, "bold")).pack(anchor="w")

    ttk.Label(
        root_frame,
        text="Add comma-separated phrases that should normalize to each sport name.",
        wraplength=560,
    ).pack(anchor="w", pady=(2, 10))

    canvas = tk.Canvas(root_frame, height=300, highlightthickness=0)
    scrollbar = ttk.Scrollbar(root_frame, orient="vertical", command=canvas.yview)
    alias_frame = ttk.Frame(canvas)
    alias_frame.bind(
        "<Configure>",
        lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.create_window((0, 0), window=alias_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    entries = {}
    row = 0
    ttk.Label(alias_frame, text="Sport", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w", padx=(0, 10))
    ttk.Label(alias_frame, text="Default phrases", font=("Segoe UI", 10, "bold")).grid(row=row, column=1, sticky="w", padx=(0, 10))
    ttk.Label(alias_frame, text="Custom phrases", font=("Segoe UI", 10, "bold")).grid(row=row, column=2, sticky="w")

    for row, (canonical, defaults) in enumerate(DEFAULT_SPORT_ALIASES.items(), start=1):
        ttk.Label(alias_frame, text=canonical, width=22).grid(row=row, column=0, sticky="nw", pady=5, padx=(0, 10))
        ttk.Label(
            alias_frame,
            text=format_aliases(defaults),
            wraplength=210,
        ).grid(row=row, column=1, sticky="nw", pady=5, padx=(0, 10))
        value = tk.StringVar(value=format_aliases(custom_aliases.get(canonical, [])))
        ttk.Entry(alias_frame, textvariable=value, width=30).grid(row=row, column=2, sticky="new", pady=5)
        entries[canonical] = value

    extra_frame = ttk.LabelFrame(root_frame, text="New Alias Group", padding=10)
    extra_frame.pack(fill="x", pady=(12, 8))
    ttk.Label(extra_frame, text="Normalize to").grid(row=0, column=0, sticky="w")
    ttk.Label(extra_frame, text="Phrases").grid(row=0, column=1, sticky="w", padx=(10, 0))

    extra_name = tk.StringVar()
    extra_values = tk.StringVar()
    ttk.Entry(extra_frame, textvariable=extra_name, width=22).grid(row=1, column=0, sticky="w")
    ttk.Entry(extra_frame, textvariable=extra_values, width=48).grid(row=1, column=1, sticky="ew", padx=(10, 0))

    log_path_var = tk.StringVar(value=str(settings.logs_dir()))
    log_frame = ttk.LabelFrame(root_frame, text="Logs", padding=10)
    log_frame.pack(fill="x", pady=(2, 10))
    ttk.Label(log_frame, text="Run logs folder").grid(row=0, column=0, sticky="w")
    ttk.Entry(log_frame, textvariable=log_path_var, width=72).grid(row=1, column=0, sticky="ew", pady=(4, 0))

    def on_save():
        next_aliases = {}
        for canonical, var in entries.items():
            aliases = parse_alias_text(var.get())
            if aliases:
                next_aliases[canonical] = aliases

        new_name = extra_name.get().strip()
        new_aliases = parse_alias_text(extra_values.get())
        if new_name and new_aliases:
            next_aliases[new_name] = new_aliases
        elif new_name or new_aliases:
            messagebox.showerror("Settings", "New alias group needs both a sport name and phrases.")
            return

        next_settings = settings.load_settings()
        next_settings["custom_sport_aliases"] = next_aliases
        next_settings["log_directory"] = log_path_var.get().strip()
        settings.save_settings(next_settings)
        messagebox.showinfo("Settings", "Settings saved. New workflow windows will use the updated aliases.")
        win.destroy()

    button_frame = ttk.Frame(root_frame)
    button_frame.pack(fill="x")
    ttk.Button(button_frame, text="Cancel", command=win.destroy).pack(side="right")
    ttk.Button(button_frame, text="Save", command=on_save).pack(side="right", padx=(0, 8))

    win.update_idletasks()
    x = parent.winfo_rootx() + parent.winfo_width() - win.winfo_width()
    y = parent.winfo_rooty() + 20
    win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    win.wait_window()
