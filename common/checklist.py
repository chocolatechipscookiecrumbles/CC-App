"""Shared checklist dialog helper."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def center_window(win):
    win.update_idletasks()

    width = win.winfo_width()
    height = win.winfo_height()

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    win.geometry(f"{width}x{height}+{x}+{y}")


def generate_checklist(title, options):
    selected_items = []
    quit_flag = False

    win = tk.Toplevel()
    win.focus_force()
    win.title(title)
    win.grab_set()
    win.resizable(False, False)

    ttk.Separator(win, orient="horizontal").pack(
        fill="x", padx=10, pady=(8, 0)
    )

    container = ttk.Frame(win)
    container.pack(fill="both", expand=True, padx=10)

    canvas = tk.Canvas(container, height=220, highlightthickness=0)

    def _on_mousewheel(event):
        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")
        else:
            canvas.yview_scroll(int(-event.delta), "units")

    canvas.focus_set()
    canvas.bind("<Enter>", lambda e: canvas.focus_set())
    canvas.bind("<MouseWheel>", _on_mousewheel)
    canvas.bind("<Button-4>", _on_mousewheel)
    canvas.bind("<Button-5>", _on_mousewheel)
    canvas.configure(yscrollincrement=4)

    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    check_vars = []

    for opt in options:
        var = tk.BooleanVar()
        chk = ttk.Checkbutton(scroll_frame, text=opt, variable=var)
        chk.pack(anchor="w", pady=2)
        check_vars.append(var)

    ttk.Separator(win, orient="horizontal").pack(
        fill="x", padx=10, pady=(0, 4)
    )

    select_all_var = tk.BooleanVar()

    def toggle_select_all():
        state = select_all_var.get()
        for var in check_vars:
            var.set(state)

    select_all = ttk.Checkbutton(
        win,
        text="Select All",
        variable=select_all_var,
        command=toggle_select_all
    )
    select_all.pack(anchor="w", padx=12, pady=(5, 0))

    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=10)

    def on_confirm():
        selected_items.clear()
        for opt, var in zip(options, check_vars):
            if var.get():
                selected_items.append(opt)
        win.destroy()

    def on_close():
        nonlocal quit_flag
        quit_flag = True
        win.unbind_all("<MouseWheel>")
        win.destroy()

    ttk.Button(btn_frame, text="Confirm", command=on_confirm, width=12).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Cancel", command=on_close, width=12).pack(side="left", padx=5)

    win.protocol("WM_DELETE_WINDOW", on_close)
    center_window(win)
    win.wait_window()

    if quit_flag:
        return 1

    return selected_items

