from . import *
from .data_extraction import generate_template_excel, fill_excel_with_data, parse_folder_toe
#from .include_client import yes_no_popup
from .choose_uni import choose_university
from programlauncher.common.pdf_manifest import build_pdf_manifest, manifest_institution_names



def ttk_on_close():
    """Handle window close event."""
    messagebox.showerror("Error", "No client selected")
    sys.exit(1)

def run_ui(include_client):
    root = tk.Tk()
    root.withdraw()

    #Choose folder path
    messagebox.showinfo("Select Folder", "Choose the folder containing NCAA FRS PDFs.")
    folder_path = filedialog.askdirectory(title="Select PDF Folder")
    if not folder_path:
        messagebox.showinfo("No folder selected", "No sample folder path, exiting program.")
        sys.exit(1)

    # collect university list
    manifest = build_pdf_manifest(folder_path)
    unis = manifest_institution_names(manifest)

    if not unis:
        messagebox.showerror("Error", "No PDFs found in the folder.")
        sys.exit(1)

    task_store = {}

    client_uni = choose_university(unis)
    if client_uni == 1:
        messagebox.showinfo("No uni saved", "No uni saved, exiting program.")
        sys.exit(1)

    def proceed():
        #setup processing win
        processing_win = tk.Toplevel(root)
        processing_win.title("")
        processing_win.geometry("300x120")
        processing_win.resizable(False, False)
        processing_win.attributes("-topmost", True)
        processing_win.grab_set()

        processing_win.update_idletasks()
        x = (processing_win.winfo_screenwidth() // 2) - 150
        y = (processing_win.winfo_screenheight() // 2) - 60
        processing_win.geometry(f"+{x}+{y}")

        label = tk.Label(processing_win, text="Processing...", font=("Helvetica", 13))
        label.pack(pady=10)

        progress = ttk.Progressbar(processing_win, mode="indeterminate")
        progress.pack(fill="x", padx=20, pady=10)
        progress.start(10)
        processing_win.protocol("WM_DELETE_WINDOW", lambda: None)

        def task():
            try:
                df, count, client_value = parse_folder_toe(folder_path, client_uni, manifest=manifest)
                task_store["df"] = df
                task_store["count"] = count
                task_store["client_value"] = client_value
            finally:
                def finalize():
                    progress.stop()
                    processing_win.destroy()


                    ifclient = include_client
                    if ifclient is None:
                        messagebox.showerror("Error", "Nothing selected, exiting program.")
                        sys.exit(1)

                    # Proceed to save file
                    messagebox.showinfo("Save File", "Choose where to save the Excel report.")
                    output_excel = filedialog.asksaveasfilename(
                        title="Save Excel File",
                        defaultextension=".xlsx",
                        filetypes=[("Excel Files", "*.xlsx")]
                    )
                    if not output_excel:
                        messagebox.showinfo("No file saved", "No file saved, exiting program.")
                        sys.exit(1)
                    generate_template_excel(output_excel, task_store['count']-1,ifclient)
                    fill_excel_with_data(task_store['df'], output_excel, client_uni, task_store["client_value"], task_store["count"])
                    messagebox.showinfo("Done", "Excel report generated successfully.")

                    root.quit()
                    root.destroy()

                root.after(10, finalize)

        threading.Thread(target=task, daemon=True).start()
    proceed()
    root.mainloop()
