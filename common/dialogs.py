"""Shared Tkinter dialog helpers."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import settings


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


def ask_pdf_folder(title="Select PDF Folder"):
    initialdir = settings.get_initial_directory("last_pdf_folder")
    kwargs = {"title": title}
    if initialdir:
        kwargs["initialdir"] = initialdir
    folder_path = filedialog.askdirectory(**kwargs)
    if folder_path:
        settings.remember_pdf_folder(folder_path)
    return folder_path


def ask_output_path(title="Save Excel File"):
    initialdir = settings.get_initial_directory("last_save_directory")
    kwargs = {
        "title": title,
        "defaultextension": ".xlsx",
        "filetypes": [("Excel Files", "*.xlsx")],
    }
    if initialdir:
        kwargs["initialdir"] = initialdir
    output_path = filedialog.asksaveasfilename(**kwargs)
    if output_path:
        settings.remember_save_path(output_path)
    return output_path


def confirm_preview(workflow, manifest, client_uni, include_client):
    peer_count = max(len(manifest) - 1, 0)
    preview_names = [record.institution_name for record in manifest[:12]]
    more = len(manifest) - len(preview_names)
    preview_lines = "\n".join(f"- {name}" for name in preview_names)
    if more > 0:
        preview_lines += f"\n- ...and {more} more"

    include_text = "Yes" if include_client else "No"
    message = (
        f"Workflow: {workflow}\n"
        f"Client: {client_uni}\n"
        f"Include client in mean / median: {include_text}\n"
        f"PDFs detected: {len(manifest)}\n"
        f"Peer institutions: {peer_count}\n\n"
        f"Detected institutions:\n{preview_lines}\n\n"
        "Continue with report generation?"
    )
    return messagebox.askokcancel("Preview Report Inputs", message)


def show_summary(summary):
    from .logging_config import log_summary

    log_summary(summary)

    duration = (
        f"{summary.duration_seconds:.1f} seconds"
        if summary.duration_seconds is not None
        else "Not recorded"
    )
    status = "Cancelled" if summary.cancelled else "Completed"

    reason_lines = []
    for reason, count in summary.reason_counts().items():
        reason_lines.append(f"- {reason}: {count}")
    reasons = "\n".join(reason_lines) if reason_lines else "- None"

    output = summary.output_path or "No workbook written"
    log_path = summary.extra.get("log_path")
    message = (
        f"Status: {status}\n"
        f"Workflow: {summary.workflow}\n"
        f"PDFs found: {summary.pdfs_found}\n"
        f"Processed: {summary.processed_count}\n"
        f"Skipped: {summary.skipped_count}\n"
        f"Duration: {duration}\n"
        f"Output: {output}\n\n"
        f"Log: {log_path or 'Not available'}\n\n"
        f"Skipped reasons:\n{reasons}"
    )
    messagebox.showinfo("Batch Summary", message)
