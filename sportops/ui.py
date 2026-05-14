from . import *

from .Excel_Generator import (
    build_totalsports_sheet,
    build_total_sports_total_sheet,
    generate_template_excel_totalsports
)
from .Folder_Parser import collect_sports_across_pdfs
from .fill_excel_with_data_sportops import fill_excel_with_data_sportops
from .choose_uni import choose_university
from .checklist import generate_checklist
#from .include_client import yes_no_popup
from programlauncher.common.pdf_manifest import build_pdf_manifest, manifest_institution_names

def ttk_on_close():
    """Handle window close event."""
    messagebox.showerror("Error", "No client selected")
    sys.exit(1)

def run_ui(include_client):
    root = tk.Tk()
    root.withdraw()

    # Choose folder path
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
                sport_dfs, men_sports, women_sports = collect_sports_across_pdfs(folder_path, manifest=manifest)
                #print(men_sports, women_sports)

            finally:
                def finalize():
                    progress.stop()
                    processing_win.destroy()

                    male_sports = generate_checklist("Male Sports", men_sports)
                    if male_sports == 1:
                        messagebox.showerror("Error", "Nothing selected, exiting program.")
                        sys.exit(1)

                    # Show Female checklist, wait until user confirms
                    #female_sports = [s for s in task_store["sportsf"] if s not in mens_only]
                    female_sports = generate_checklist("Female Sports", women_sports)

                    if female_sports == 1:
                        messagebox.showerror("Error", "Nothing selected, exiting program.")
                        sys.exit(1)
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
                    generate_template_excel_totalsports(output_excel)
                    #generate_template_excel_scholar(output_excel, task_store['count']-1, male_sports, female_sports)
                    '''fill_excel_with_data_scholar(task_store['male_df'], task_store['female_df'], output_excel,
                                                 client_uni)'''
                    fill_excel_with_data_sportops(sport_dfs, output_excel, client_uni, male_sports, female_sports,ifclient)
                    messagebox.showinfo("Done", "Excel report generated successfully.")

                    root.quit()
                    root.destroy()

                root.after(10, finalize)
        threading.Thread(target=task, daemon=True).start()
    proceed()
    root.mainloop()
