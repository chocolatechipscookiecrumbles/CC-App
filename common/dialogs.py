"""Shared Tkinter dialog helpers."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk


def choose_university(unis, folder_path=None):
    """
    Open a popup to select a university.

    Returns the selected university string, or 1 if the window is canceled.
    The folder_path argument is accepted for compatibility with the old helpers.
    """
    quit_flag = False

    select_win = tk.Toplevel()
    select_win.title("Select Client University")
    select_win.geometry("300x130")
    select_win.resizable(False, False)
    select_win.attributes("-topmost", True)
    x = (select_win.winfo_screenwidth() // 2) - 150
    y = (select_win.winfo_screenheight() // 2) - 60
    select_win.geometry(f"+{x}+{y}")

    uni_var = tk.StringVar(value=unis[0])
    tk.Label(select_win, text="Choose Client University:").pack(pady=5)
    dropdown = ttk.Combobox(select_win, textvariable=uni_var, values=unis, state="readonly")
    dropdown.pack(pady=5)

    if unis:
        uni_var.set(unis[0])
        dropdown.set(unis[0])
        select_win.update_idletasks()

    def on_ok():
        if not uni_var.get():
            messagebox.showerror("Error", "No client selected.")
        select_win.destroy()

    def on_close():
        nonlocal quit_flag
        quit_flag = True
        select_win.destroy()

    select_win.protocol("WM_DELETE_WINDOW", on_close)
    tk.Button(select_win, text="OK", command=on_ok).pack(pady=10)
    select_win.wait_window(select_win)

    if quit_flag:
        return 1

    return uni_var.get()


def yes_no_popup(message="Include client in mean and median?", title="Confirmation"):
    """
    Modal Yes/No popup.

    Returns True for Yes, False for No, and None if the window is closed.
    """
    response = None
    quit_flag = False

    win = tk.Toplevel()
    win.title(title)
    win.grab_set()

    tk.Label(win, text=message, wraplength=250, justify="center").pack(pady=15)

    def on_yes():
        nonlocal response
        response = True
        win.destroy()

    def on_no():
        nonlocal response
        response = False
        win.destroy()

    def on_close():
        nonlocal quit_flag
        quit_flag = True
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)

    button_frame = tk.Frame(win)
    button_frame.pack(pady=5)
    tk.Button(button_frame, text="Yes", width=10, command=on_yes).pack(side="left", padx=10)
    tk.Button(button_frame, text="No", width=10, command=on_no).pack(side="right", padx=10)

    win.update_idletasks()
    win_width = 300
    win_height = win.winfo_reqheight()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = int((screen_width / 2) - (win_width / 2))
    y = int((screen_height / 2) - (win_height / 2))

    win.geometry(f"{win_width}x{win_height}+{x}+{y}")
    win.wait_window()

    if quit_flag:
        return None

    return response

