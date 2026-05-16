"""Tkinter settings dialog for app preferences."""

from __future__ import annotations

from dataclasses import dataclass, field
import tkinter as tk
from tkinter import messagebox, ttk

from . import settings
from .sports import DEFAULT_SPORT_ALIASES


ALIAS_TABLE_COLUMNS = (210, 520)


@dataclass
class AliasRowState:
    canonical_var: object
    aliases_var: object
    deleted: bool = False
    frame: object | None = None
    widgets: list[object] = field(default_factory=list)


@dataclass
class SportOpsTableRowState:
    number_var: object
    name_var: object
    enabled_var: object
    is_default: bool = False
    deleted: bool = False
    frame: object | None = None
    widgets: list[object] = field(default_factory=list)


def parse_alias_text(value: str) -> list[str]:
    return dedupe_aliases(part.strip() for part in value.split(","))


def dedupe_aliases(values) -> list[str]:
    seen = set()
    aliases = []
    for value in values:
        alias = str(value).strip()
        if not alias:
            continue
        key = alias.casefold()
        if key in seen:
            continue
        seen.add(key)
        aliases.append(alias)
    return aliases


def format_aliases(values: list[str]) -> str:
    return ", ".join(values)


def is_dark_color(widget, color: str) -> bool:
    try:
        red, green, blue = widget.winfo_rgb(color)
    except tk.TclError:
        return False
    luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 65535
    return luminance < 0.45


def theme_colors(widget) -> dict[str, str]:
    style = ttk.Style(widget)
    frame_bg = (
        style.lookup("TFrame", "background")
        or style.lookup("TLabel", "background")
        or widget.winfo_toplevel().cget("background")
    )
    field_bg = style.lookup("TEntry", "fieldbackground") or frame_bg
    foreground = style.lookup("TEntry", "foreground") or ("#f2f2f2" if is_dark_color(widget, field_bg) else "#1f1f1f")
    selected_bg = style.lookup("Treeview", "selectbackground", ("selected",)) or "#5b7fb9"
    selected_fg = style.lookup("Treeview", "selectforeground", ("selected",)) or "#ffffff"
    border = style.lookup("TSeparator", "background") or ("#5a5a5a" if is_dark_color(widget, frame_bg) else "#d8d8d8")
    warning = "#f2b84b" if is_dark_color(widget, frame_bg) else "#8a5a00"
    return {
        "frame_bg": frame_bg,
        "field_bg": field_bg,
        "foreground": foreground,
        "selected_bg": selected_bg,
        "selected_fg": selected_fg,
        "border": border,
        "warning": warning,
    }


def collect_alias_settings(row_states):
    next_aliases = {}
    canonical_lookup = {}
    for row_state in row_states:
        if row_state.deleted:
            continue

        canonical = row_state.canonical_var.get().strip()
        aliases = parse_alias_text(row_state.aliases_var.get())
        if not canonical or not aliases:
            continue

        canonical_key = canonical.casefold()
        target = canonical_lookup.setdefault(canonical_key, canonical)
        if target in next_aliases:
            next_aliases[target] = dedupe_aliases(next_aliases[target] + aliases)
        else:
            next_aliases[target] = aliases

    return next_aliases


def build_alias_tab(parent, custom_aliases):
    tab = ttk.Frame(parent, padding=12)
    colors = theme_colors(tab)

    ttk.Label(tab, text="Sport Aliases", font=("Segoe UI", 14, "bold")).pack(anchor="w")
    instructions = (
        "Use this table to standardize sport names across the whole app. "
        "Enter PDF phrases separated by commas. "
        "Example: TrackandField, Track and Field, Cross Country normalizes to XC/TF."
    )
    ttk.Label(tab, text=instructions, wraplength=800).pack(anchor="w", pady=(2, 4))
    ttk.Label(
        tab,
        text=(
            "Changes appear immediately, but are not saved until you click Save. "
            "To remove a row, select it and use Delete Selected."
        ),
        foreground=colors["warning"],
        wraplength=800,
    ).pack(anchor="w", pady=(0, 10))

    table_shell = ttk.Frame(tab)
    table_shell.pack(fill="both", expand=True)

    header = ttk.Frame(table_shell)
    header.pack(fill="x", padx=(0, 18))
    for index, label in enumerate(("Normalized Sport", "PDF Phrases")):
        ttk.Label(header, text=label, font=("Segoe UI", 10, "bold"), width=1).grid(
            row=0,
            column=index,
            sticky="ew",
            padx=(0, 6),
        )
    header.grid_columnconfigure(0, minsize=ALIAS_TABLE_COLUMNS[0], weight=0)
    header.grid_columnconfigure(1, minsize=ALIAS_TABLE_COLUMNS[1], weight=1)

    canvas = tk.Canvas(
        table_shell,
        height=220,
        background=colors["frame_bg"],
        highlightthickness=1,
        highlightbackground=colors["border"],
    )
    scrollbar = ttk.Scrollbar(table_shell, orient="vertical", command=canvas.yview)
    rows_frame = tk.Frame(canvas, bg=colors["frame_bg"])
    canvas_window = canvas.create_window((0, 0), window=rows_frame, anchor="nw")

    def on_rows_configure(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_canvas_configure(event):
        canvas.itemconfigure(canvas_window, width=event.width)

    rows_frame.bind("<Configure>", on_rows_configure)
    canvas.bind("<Configure>", on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    rows_frame.grid_columnconfigure(0, minsize=ALIAS_TABLE_COLUMNS[0], weight=0)
    rows_frame.grid_columnconfigure(1, minsize=ALIAS_TABLE_COLUMNS[1], weight=1)

    row_states = []
    row_index = {"value": 0}
    selected_state = {"value": None}
    delete_button = {"widget": None}

    def apply_row_selection(next_state):
        selected_state["value"] = next_state
        for state in row_states:
            if state.deleted or state.frame is None:
                continue
            is_selected = state is next_state
            bg = colors["selected_bg"] if is_selected else colors["frame_bg"]
            entry_bg = colors["selected_bg"] if is_selected else colors["field_bg"]
            fg = colors["selected_fg"] if is_selected else colors["foreground"]
            state.frame.configure(bg=bg)
            for child in state.widgets:
                child.configure(
                    bg=entry_bg,
                    fg=fg,
                    insertbackground=fg,
                    readonlybackground=entry_bg,
                    selectbackground=colors["selected_bg"],
                    selectforeground=colors["selected_fg"],
                )
        if delete_button["widget"] is not None:
            delete_button["widget"].configure(state="normal" if next_state is not None else "disabled")

    def bind_row_selection(widget, state):
        widget.bind("<Button-1>", lambda _event: apply_row_selection(state), add="+")

    def add_alias_row(canonical, aliases=None):
        row = row_index["value"]
        row_index["value"] += 1

        canonical_var = tk.StringVar(value=canonical)
        aliases_var = tk.StringVar(value=format_aliases(aliases or []))
        row_frame = tk.Frame(rows_frame, bg=colors["frame_bg"], padx=2, pady=4)
        state = AliasRowState(canonical_var, aliases_var, frame=row_frame)
        row_states.append(state)

        row_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        row_frame.grid_columnconfigure(0, minsize=ALIAS_TABLE_COLUMNS[0], weight=0)
        row_frame.grid_columnconfigure(1, minsize=ALIAS_TABLE_COLUMNS[1], weight=1)

        entry_options = {
            "bg": colors["field_bg"],
            "fg": colors["foreground"],
            "insertbackground": colors["foreground"],
            "selectbackground": colors["selected_bg"],
            "selectforeground": colors["selected_fg"],
            "relief": "flat",
            "highlightthickness": 1,
            "highlightbackground": colors["border"],
            "highlightcolor": colors["selected_bg"],
        }

        canonical_entry = tk.Entry(row_frame, textvariable=canonical_var, **entry_options)
        canonical_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=3)
        aliases_entry = tk.Entry(row_frame, textvariable=aliases_var, **entry_options)
        aliases_entry.grid(row=0, column=1, sticky="ew", ipady=3)
        state.widgets = [canonical_entry, aliases_entry]

        for widget in (row_frame, canonical_entry, aliases_entry):
            bind_row_selection(widget, state)

        return state

    def delete_selected():
        state = selected_state["value"]
        if state is None:
            return
        if not messagebox.askyesno(
            "Delete Alias Group",
            "Delete this alias group from the table? Click Save to persist the deletion.",
        ):
            return
        state.deleted = True
        if state.frame is not None:
            state.frame.destroy()
        apply_row_selection(None)

    for canonical, aliases in custom_aliases.items():
        add_alias_row(canonical, aliases=aliases)

    action_frame = ttk.Frame(tab)
    action_frame.pack(fill="x", pady=(8, 0))
    delete_button["widget"] = ttk.Button(
        action_frame,
        text="Delete Selected",
        command=delete_selected,
        state="disabled",
    )
    delete_button["widget"].pack(side="left")

    extra_frame = ttk.LabelFrame(tab, text="New Alias Group", padding=10)
    extra_frame.pack(fill="x", pady=(12, 0))
    ttk.Label(extra_frame, text="Use this for a sport name not already listed above.").grid(
        row=0,
        column=0,
        columnspan=3,
        sticky="w",
        pady=(0, 8),
    )
    ttk.Label(extra_frame, text="Normalized Sport").grid(row=1, column=0, sticky="w")
    ttk.Label(extra_frame, text="PDF Phrases").grid(row=1, column=1, sticky="w", padx=(10, 0))

    extra_name = tk.StringVar()
    extra_values = tk.StringVar()
    ttk.Entry(extra_frame, textvariable=extra_name, width=22).grid(row=2, column=0, sticky="w")
    ttk.Entry(extra_frame, textvariable=extra_values, width=58).grid(row=2, column=1, sticky="ew", padx=(10, 0))

    def add_new_group():
        new_name = extra_name.get().strip()
        new_aliases = parse_alias_text(extra_values.get())
        if not new_name or not new_aliases:
            messagebox.showerror("Settings", "New alias group needs both a sport name and phrases.")
            return

        for state in row_states:
            if state.deleted:
                continue
            if state.canonical_var.get().strip().casefold() == new_name.casefold():
                merged = dedupe_aliases(parse_alias_text(state.aliases_var.get()) + new_aliases)
                state.aliases_var.set(format_aliases(merged))
                apply_row_selection(state)
                break
        else:
            apply_row_selection(add_alias_row(new_name, aliases=new_aliases))

        extra_name.set("")
        extra_values.set("")
        messagebox.showwarning(
            "Unsaved Alias Change",
            "The alias group has been added to the table. Click Save to persist this change.",
        )

    ttk.Button(extra_frame, text="Add to Table", command=add_new_group).grid(
        row=2,
        column=2,
        sticky="e",
        padx=(10, 0),
    )
    extra_frame.grid_columnconfigure(1, weight=1)

    return tab, row_states


def build_logs_tab(parent, current_settings):
    tab = ttk.Frame(parent, padding=12)

    ttk.Label(tab, text="Logs", font=("Segoe UI", 14, "bold")).pack(anchor="w")
    ttk.Label(
        tab,
        text=(
            "Run logs are created once per workflow run. "
            "Skipped CSVs are saved separately in the selected PDF folder only when files are skipped."
        ),
        wraplength=760,
    ).pack(anchor="w", pady=(2, 14))

    default_path = str(settings.default_logs_dir())
    current_path = str(settings.logs_dir())

    path_frame = ttk.LabelFrame(tab, text="Run Logs Folder", padding=10)
    path_frame.pack(fill="x")
    ttk.Label(path_frame, text="Current resolved path").grid(row=0, column=0, sticky="w")
    current_path_var = tk.StringVar(value=current_path)
    ttk.Entry(path_frame, textvariable=current_path_var, width=86, state="readonly").grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(4, 10),
    )

    ttk.Label(path_frame, text="Custom log directory").grid(row=2, column=0, sticky="w")
    log_path_var = tk.StringVar(value=current_settings.get("log_directory", ""))
    ttk.Entry(path_frame, textvariable=log_path_var, width=72).grid(row=3, column=0, sticky="ew", pady=(4, 0))

    def refresh_current_path(*_):
        custom_path = log_path_var.get().strip()
        current_path_var.set(custom_path or default_path)

    log_path_var.trace_add("write", refresh_current_path)

    def use_default():
        log_path_var.set("")
        current_path_var.set(default_path)

    def copy_path():
        tab.clipboard_clear()
        tab.clipboard_append(current_path_var.get())
        messagebox.showinfo("Logs", "Log path copied to clipboard.")

    button_frame = ttk.Frame(path_frame)
    button_frame.grid(row=3, column=1, sticky="e", padx=(8, 0))
    ttk.Button(button_frame, text="Use Default", command=use_default).pack(side="left")
    ttk.Button(button_frame, text="Copy Path", command=copy_path).pack(side="left", padx=(6, 0))

    ttk.Label(path_frame, text=f"Default: {default_path}", wraplength=740).grid(
        row=4,
        column=0,
        columnspan=2,
        sticky="w",
        pady=(10, 0),
    )
    path_frame.grid_columnconfigure(0, weight=1)

    return tab, log_path_var


def build_sportops_tables_tab(parent, table_map, selected_table_ids):
    from programlauncher.sportops.config import SPORTOPS_TABLES

    tab = ttk.Frame(parent, padding=12)
    colors = theme_colors(tab)
    selected_table_ids = {str(table_id) for table_id in selected_table_ids}

    ttk.Label(tab, text="SportOps Tables", font=("Segoe UI", 14, "bold")).pack(anchor="w")
    ttk.Label(
        tab,
        text=(
            "Choose which SportOps NCAA expense tables are parsed and included in the final workbook. "
            "Default rows can be unchecked, but only added rows can be deleted. "
            "Reset restores the original built-in table list."
        ),
        wraplength=800,
    ).pack(anchor="w", pady=(2, 10))

    table_shell = ttk.Frame(tab)
    table_shell.pack(fill="both", expand=True)

    header = ttk.Frame(table_shell)
    header.pack(fill="x", padx=(0, 18))
    for index, label in enumerate(("Use", "Table Number", "Table Name")):
        ttk.Label(header, text=label, font=("Segoe UI", 10, "bold"), width=1).grid(
            row=0,
            column=index,
            sticky="ew",
            padx=(0, 6),
        )
    header.grid_columnconfigure(0, minsize=54, weight=0)
    header.grid_columnconfigure(1, minsize=150, weight=0)
    header.grid_columnconfigure(2, minsize=500, weight=1)

    canvas = tk.Canvas(
        table_shell,
        height=260,
        background=colors["frame_bg"],
        highlightthickness=1,
        highlightbackground=colors["border"],
    )
    scrollbar = ttk.Scrollbar(table_shell, orient="vertical", command=canvas.yview)
    rows_frame = tk.Frame(canvas, bg=colors["frame_bg"])
    canvas_window = canvas.create_window((0, 0), window=rows_frame, anchor="nw")

    def on_rows_configure(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_canvas_configure(event):
        canvas.itemconfigure(canvas_window, width=event.width)

    rows_frame.bind("<Configure>", on_rows_configure)
    canvas.bind("<Configure>", on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    rows_frame.grid_columnconfigure(0, minsize=54, weight=0)
    rows_frame.grid_columnconfigure(1, minsize=150, weight=0)
    rows_frame.grid_columnconfigure(2, minsize=500, weight=1)

    row_states = []
    row_index = {"value": 0}
    selected_state = {"value": None}
    delete_button = {"widget": None}

    def apply_row_selection(next_state):
        selected_state["value"] = next_state
        for state in row_states:
            if state.deleted or state.frame is None:
                continue
            is_selected = state is next_state
            bg = colors["selected_bg"] if is_selected else colors["frame_bg"]
            entry_bg = colors["selected_bg"] if is_selected else colors["field_bg"]
            fg = colors["selected_fg"] if is_selected else colors["foreground"]
            state.frame.configure(bg=bg)
            for child in state.widgets:
                child.configure(
                    bg=entry_bg,
                    fg=fg,
                    insertbackground=fg,
                    selectbackground=colors["selected_bg"],
                    selectforeground=colors["selected_fg"],
                )
        if delete_button["widget"] is not None:
            delete_button["widget"].configure(state="normal" if next_state is not None else "disabled")

    def bind_row_selection(widget, state):
        widget.bind("<Button-1>", lambda _event: apply_row_selection(state), add="+")

    def add_table_row(table_id, label, enabled=True, is_default=False):
        row = row_index["value"]
        row_index["value"] += 1

        number_var = tk.StringVar(value=table_id)
        name_var = tk.StringVar(value=label)
        enabled_var = tk.BooleanVar(value=enabled)
        row_frame = tk.Frame(rows_frame, bg=colors["frame_bg"], padx=2, pady=4)
        state = SportOpsTableRowState(
            number_var,
            name_var,
            enabled_var,
            is_default=is_default,
            frame=row_frame,
        )
        row_states.append(state)

        row_frame.grid(row=row, column=0, columnspan=3, sticky="ew")
        row_frame.grid_columnconfigure(0, minsize=54, weight=0)
        row_frame.grid_columnconfigure(1, minsize=150, weight=0)
        row_frame.grid_columnconfigure(2, minsize=500, weight=1)

        entry_options = {
            "bg": colors["field_bg"],
            "fg": colors["foreground"],
            "insertbackground": colors["foreground"],
            "relief": "flat",
            "highlightthickness": 1,
            "highlightbackground": colors["border"],
            "highlightcolor": colors["selected_bg"],
        }
        use_checkbox = ttk.Checkbutton(row_frame, variable=enabled_var)
        use_checkbox.grid(row=0, column=0, sticky="w", padx=(0, 8))
        number_entry = tk.Entry(row_frame, textvariable=number_var, **entry_options)
        number_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), ipady=3)
        if is_default:
            number_entry.configure(state="readonly", readonlybackground=colors["field_bg"])
        name_entry = tk.Entry(row_frame, textvariable=name_var, **entry_options)
        name_entry.grid(row=0, column=2, sticky="ew", ipady=3)
        state.widgets = [number_entry, name_entry]

        for widget in (row_frame, use_checkbox, number_entry, name_entry):
            bind_row_selection(widget, state)
        return state

    for table_id, label in table_map.items():
        add_table_row(
            table_id,
            label,
            enabled=str(table_id) in selected_table_ids,
            is_default=str(table_id) in SPORTOPS_TABLES,
        )

    action_frame = ttk.Frame(tab)
    action_frame.pack(fill="x", pady=(8, 0))

    def delete_selected():
        state = selected_state["value"]
        if state is None:
            return
        if state.is_default:
            messagebox.showwarning(
                "Default SportOps Table",
                "Built-in SportOps tables can be unchecked, but they cannot be deleted. "
                "Use Reset to Defaults to restore the original list.",
            )
            return
        if not messagebox.askyesno(
            "Delete SportOps Table",
            "Delete this table from the editable list? Click Save to persist the deletion.",
        ):
            return
        state.deleted = True
        if state.frame is not None:
            state.frame.destroy()
        apply_row_selection(None)

    def reset_defaults():
        if not messagebox.askyesno(
            "Reset SportOps Tables",
            "Reset SportOps tables to the built-in defaults? Click Save to persist this reset.",
        ):
            return
        for state in row_states:
            state.deleted = True
            if state.frame is not None:
                state.frame.destroy()
        apply_row_selection(None)
        row_index["value"] = 0
        for table_id, label in SPORTOPS_TABLES.items():
            add_table_row(table_id, label, enabled=True, is_default=True)

    delete_button["widget"] = ttk.Button(
        action_frame,
        text="Delete Selected",
        command=delete_selected,
        state="disabled",
    )
    delete_button["widget"].pack(side="left")
    ttk.Button(action_frame, text="Reset to Defaults", command=reset_defaults).pack(side="left", padx=(8, 0))

    extra_frame = ttk.LabelFrame(tab, text="New SportOps Table", padding=10)
    extra_frame.pack(fill="x", pady=(12, 0))
    ttk.Label(extra_frame, text="Use this for a SportOps table not already listed above.").grid(
        row=0,
        column=0,
        columnspan=3,
        sticky="w",
        pady=(0, 8),
    )
    ttk.Label(extra_frame, text="Table Number").grid(row=1, column=0, sticky="w")
    ttk.Label(extra_frame, text="Table Name").grid(row=1, column=1, sticky="w", padx=(10, 0))
    extra_number = tk.StringVar()
    extra_name = tk.StringVar()
    ttk.Entry(extra_frame, textvariable=extra_number, width=18).grid(row=2, column=0, sticky="w")
    ttk.Entry(extra_frame, textvariable=extra_name, width=60).grid(row=2, column=1, sticky="ew", padx=(10, 0))

    def add_new_table():
        table_id = extra_number.get().strip()
        label = extra_name.get().strip()
        if not table_id or not label:
            messagebox.showerror("SportOps Tables", "New table needs both a table number and table name.")
            return
        for state in row_states:
            if state.deleted:
                continue
            if state.number_var.get().strip().casefold() == table_id.casefold():
                state.number_var.set(table_id)
                state.name_var.set(label)
                state.enabled_var.set(True)
                apply_row_selection(state)
                break
        else:
            apply_row_selection(add_table_row(table_id, label, enabled=True, is_default=False))
        extra_number.set("")
        extra_name.set("")
        messagebox.showwarning(
            "Unsaved SportOps Table Change",
            "The table has been added to the editable list. Click Save to persist this change.",
        )

    ttk.Button(extra_frame, text="Add to Table", command=add_new_table).grid(
        row=2,
        column=2,
        sticky="e",
        padx=(10, 0),
    )
    extra_frame.grid_columnconfigure(1, weight=1)

    return tab, row_states


def collect_sportops_table_settings(row_states):
    table_map = {}
    selected_ids = []
    seen = set()
    for state in row_states:
        if state.deleted:
            continue
        table_id = state.number_var.get().strip()
        label = state.name_var.get().strip()
        if not table_id or not label:
            continue
        key = table_id.casefold()
        if key in seen:
            continue
        seen.add(key)
        table_map[table_id] = label
        if state.enabled_var.get():
            selected_ids.append(table_id)
    return table_map, selected_ids


def open_settings_dialog(parent):
    from programlauncher.sportops.config import SPORTOPS_TABLES

    current_settings = settings.load_settings()
    sport_aliases = settings.get_sport_aliases(DEFAULT_SPORT_ALIASES)
    sportops_table_map = settings.get_sportops_tables(SPORTOPS_TABLES)
    sportops_selected_tables = settings.get_sportops_output_tables(list(sportops_table_map))

    win = tk.Toplevel(parent)
    win.title("Settings")
    win.geometry("920x720")
    win.minsize(840, 640)
    win.transient(parent)
    win.grab_set()

    root_frame = ttk.Frame(win, padding=14)
    root_frame.pack(fill="both", expand=True)
    root_frame.grid_columnconfigure(0, weight=1)
    root_frame.grid_rowconfigure(0, weight=1)

    notebook = ttk.Notebook(root_frame)
    notebook.grid(row=0, column=0, sticky="nsew")

    alias_tab, row_states = build_alias_tab(notebook, sport_aliases)
    sportops_tables_tab, sportops_table_rows = build_sportops_tables_tab(
        notebook,
        sportops_table_map,
        sportops_selected_tables,
    )
    logs_tab, log_path_var = build_logs_tab(notebook, current_settings)
    notebook.add(alias_tab, text="Sport Aliases")
    notebook.add(sportops_tables_tab, text="SportOps Tables")
    notebook.add(logs_tab, text="Logs")

    def on_save():
        next_aliases = collect_alias_settings(row_states)
        next_sportops_tables, next_sportops_selected_tables = collect_sportops_table_settings(sportops_table_rows)
        if not next_sportops_tables:
            if not messagebox.askyesno(
                "SportOps Tables",
                "No SportOps tables remain in the table. Reset SportOps tables to defaults instead?",
            ):
                return
            next_sportops_tables = dict(SPORTOPS_TABLES)
            next_sportops_selected_tables = list(SPORTOPS_TABLES)
        elif not next_sportops_selected_tables:
            if not messagebox.askyesno(
                "SportOps Tables",
                "No SportOps tables are selected for output. Reset selections to the built-in defaults instead?",
            ):
                return
            next_sportops_selected_tables = list(SPORTOPS_TABLES)

        next_settings = settings.load_settings()
        next_settings["sport_aliases"] = next_aliases
        next_settings["sportops_tables"] = next_sportops_tables
        next_settings["sportops_output_tables"] = next_sportops_selected_tables
        next_settings["log_directory"] = log_path_var.get().strip()
        settings.save_settings(next_settings)
        messagebox.showinfo("Settings", "Settings saved. This window will remain open for more changes.")

    button_frame = ttk.Frame(root_frame)
    button_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
    ttk.Button(button_frame, text="Cancel", command=win.destroy).pack(side="right")
    ttk.Button(button_frame, text="Save", command=on_save).pack(side="right", padx=(0, 8))

    win.update_idletasks()
    x = parent.winfo_rootx() + parent.winfo_width() - win.winfo_width()
    y = parent.winfo_rooty() + 20
    win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    win.wait_window()
