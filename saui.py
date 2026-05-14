import tkinter as tk
from tkinter import messagebox, ttk
import multiprocessing
from programlauncher.common import settings

def center_window(win):
    win.update_idletasks()  # ensure geometry is calculated

    width = win.winfo_width()
    height = win.winfo_height()

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    win.geometry(f"{width}x{height}+{x}+{y}")

# --- Program wrappers ---
def run_scholar(include_client):
    try:
        from programlauncher.scholar import run_ui
        run_ui(include_client)
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Scholar Error", f"Error running Scholar:\n{str(e)}")
        root.destroy()

def run_revenue(include_client):
    try:
        from programlauncher.rev import run_ui
        run_ui(include_client)
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Revenue Error", f"Error running Revenue:\n{str(e)}")
        root.destroy()

def run_sportops(include_client):
    try:
        from programlauncher.sportops import run_ui
        run_ui(include_client)
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Sport Ops Error", f"Error running Sport Ops:\n{str(e)}")
        root.destroy()

def run_toe(include_client):
    try:
        from programlauncher.toe import run_ui
        run_ui(include_client)
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("TOE Error", f"Error running TOE:\n{str(e)}")
        root.destroy()

def launch_program(name, all_buttons, include_client, dropdown):
    program_map = {
        "Scholar": run_scholar,
        "Sport Ops": run_sportops,
        "Revenue": run_revenue,
        "TOE": run_toe
    }

    func = program_map.get(name)
    if not func:
        messagebox.showerror("Error", f"No program found for {name}")
        return


    # Disable all buttons + dropdown immediately
    for btn in all_buttons:
        btn.config(state="disabled")
        if btn['text'] == name:
            clicked_btn = btn
            btn.config(relief="sunken", bg="#a0a0a0")
            btn.update_idletasks()  # <-- force redraw
    dropdown.config(state="disabled")

    # Launch program in separate process
    process = multiprocessing.Process(target=func, args=(include_client,))
    process.start()

    # Poll process using after (non-blocking)
    def check_process():
        if process.is_alive():
            all_buttons[0].after(200, check_process)
        else:
            for btn in all_buttons:
                btn.config(
                    state="normal",
                    bg=btn.default_bg, # restore to default window background
                    relief="raised",
                    bd=2,
                    highlightthickness=1,
                    highlightbackground="#000",  # ensures outline on Windows
                    activebackground="#c0c0c0",
                )
            dropdown.config(state="readonly")

    all_buttons[0].after(200, check_process)


def create_launcher_ui():
    """Create and run the launcher UI"""

    def get_include_client_flag():
        include_client = True if include_var.get() == "Yes" else False
        settings.remember_include_client(include_client)
        return include_client


    # ------------------ Root ------------------
    root = tk.Tk()
    root.title("Program Launcher")
    #root.geometry("400x450")
    root.resizable(False, False)

    # --- CREATE STYLE HERE ---
    style = ttk.Style()
    style.configure("Launcher.TButton",
                    font=("Segoe UI", 20, "bold"),
                    padding=(10, 10))  # left/right, top/bottom padding

    # ------------------ Main Card ------------------
    main_frame = tk.Frame(
        root,
    )
    main_frame.pack(fill="both", expand=True, padx=25, pady=30)

    # ------------------ Title ------------------
    tk.Label(
        main_frame,
        text="NCAA Report Tool",
        font=("Segoe UI", 22, "bold"),
    ).pack(pady=(2, 8))

    # ---------------- Include Client Dropdown ----------------
    include_frame = ttk.Frame(main_frame)
    include_frame.pack(fill="x", padx=12, pady=(4, 12))

    ttk.Label(
        include_frame,
        text="Include client in mean / median?"
    ).pack(side="left")

    default_include = settings.load_settings().get("last_include_client", True)
    include_var = tk.StringVar(value="Yes" if default_include else "No")

    include_dropdown = ttk.Combobox(
        include_frame,
        textvariable=include_var,
        values=["Yes", "No"],
        state="readonly",
        width=3
    )
    include_dropdown.pack(side="left", padx=(10, 10))

    # ------------------ Buttons ------------------
    button_frame = tk.Frame(main_frame)
    button_frame.pack()

    programs = ["Scholar", "Sport Ops", "Revenue", "TOE"]
    all_buttons = []

    def make_button(parent, name):
        def on_click():
            launch_program(name, all_buttons, get_include_client_flag(), include_dropdown)

        btn = tk.Button(
            parent,
            text=name,
            font=("Segoe UI", 20, "bold"),
            width=12,
            height=2,  # slightly taller for Windows
            relief="raised",
            bd=2,
            highlightthickness=1,
            highlightbackground="#000",  # ensures outline on Windows
            activebackground="#c0c0c0",
            command=on_click
        )
        btn.default_bg = btn.cget("bg")
        #btn = ttk.Button(parent, text=name, style="Launcher.TButton", command=on_click,highlightthickness = 1)
        return btn

    for program in programs:
        button = make_button(button_frame, program)
        #button.pack(pady=8)
        button.pack(fill = 'x', pady = 8, expand = True)
        all_buttons.append(button)

    #center_window(root)
    root.mainloop()

def main():
    """Main function - entry point"""
    multiprocessing.freeze_support()
    create_launcher_ui()

if __name__ == '__main__':
    main()
