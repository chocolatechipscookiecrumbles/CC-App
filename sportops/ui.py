from . import *
import queue

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
from programlauncher.common.dialogs import (
    ask_output_path,
    ask_pdf_folder,
    confirm_preview,
    show_summary,
)
from programlauncher.common.pdf_manifest import build_pdf_manifest, manifest_institution_names
from programlauncher.common.logging_config import log_exception, start_run_log
from programlauncher.common.progress import CancellationToken, ProcessingDialog, ProgressReporter
from programlauncher.common.run_summary import WorkflowRunSummary

def ttk_on_close():
    """Handle window close event."""
    messagebox.showerror("Error", "No client selected")
    sys.exit(1)

def run_ui(include_client):
    root = tk.Tk()
    root.withdraw()

    # Choose folder path
    messagebox.showinfo("Select Folder", "Choose the folder containing NCAA FRS PDFs.")
    folder_path = ask_pdf_folder(title="Select PDF Folder")
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

    if not confirm_preview("Sport Ops", manifest, client_uni, include_client):
        messagebox.showinfo("Cancelled", "Report generation cancelled.")
        sys.exit(0)

    def proceed():
        summary = WorkflowRunSummary(
            "Sport Ops",
            folder_path,
            pdfs_found=len(manifest),
            extra={"client": client_uni, "include_client": include_client},
        )
        start_run_log(summary)
        progress_queue = queue.Queue()
        cancel_token = CancellationToken()
        processing_dialog = ProcessingDialog(
            root,
            "Processing Sport Ops",
            progress_queue,
            cancel_token,
        )
        reporter = ProgressReporter(progress_queue.put)
        task_store["error"] = None

        def task():
            try:
                sport_dfs, men_sports, women_sports = collect_sports_across_pdfs(
                    folder_path,
                    manifest=manifest,
                    summary=summary,
                    progress_reporter=reporter,
                    cancel_token=cancel_token,
                )
                task_store.update({
                    "sport_dfs": sport_dfs,
                    "men_sports": men_sports,
                    "women_sports": women_sports,
                })
                #print(men_sports, women_sports)

            except Exception as exc:
                task_store["error"] = exc
            finally:
                def finalize():
                    processing_dialog.destroy()

                    if task_store["error"]:
                        summary.finish(cancelled=cancel_token.is_cancelled)
                        log_exception(summary, task_store["error"])
                        messagebox.showerror("Error", f"Sport Ops processing failed:\n{task_store['error']}")
                        show_summary(summary)
                        root.quit()
                        root.destroy()
                        return

                    if cancel_token.is_cancelled or summary.cancelled:
                        summary.finish(cancelled=True)
                        show_summary(summary)
                        root.quit()
                        root.destroy()
                        return

                    male_sports = generate_checklist("Male Sports", task_store["men_sports"])
                    if male_sports == 1:
                        messagebox.showerror("Error", "Nothing selected, exiting program.")
                        sys.exit(1)

                    # Show Female checklist, wait until user confirms
                    #female_sports = [s for s in task_store["sportsf"] if s not in mens_only]
                    female_sports = generate_checklist("Female Sports", task_store["women_sports"])

                    if female_sports == 1:
                        messagebox.showerror("Error", "Nothing selected, exiting program.")
                        sys.exit(1)
                    ifclient = include_client
                    if ifclient is None:
                        messagebox.showerror("Error", "Nothing selected, exiting program.")
                        sys.exit(1)

                    # Proceed to save file
                    messagebox.showinfo("Save File", "Choose where to save the Excel report.")
                    output_excel = ask_output_path(title="Save Excel File")
                    if not output_excel:
                        messagebox.showinfo("No file saved", "No file saved, exiting program.")
                        summary.finish(cancelled=True)
                        show_summary(summary)
                        sys.exit(1)
                    reporter.update(
                        current=len(manifest),
                        total=len(manifest),
                        institution=client_uni,
                        stage="Writing workbook",
                        skipped_count=summary.skipped_count,
                    )
                    generate_template_excel_totalsports(output_excel)
                    #generate_template_excel_scholar(output_excel, task_store['count']-1, male_sports, female_sports)
                    '''fill_excel_with_data_scholar(task_store['male_df'], task_store['female_df'], output_excel,
                                                 client_uni)'''
                    fill_excel_with_data_sportops(task_store["sport_dfs"], output_excel, client_uni, male_sports, female_sports,ifclient)
                    summary.finish(output_path=output_excel)
                    show_summary(summary)
                    messagebox.showinfo("Done", "Excel report generated successfully.")

                    root.quit()
                    root.destroy()

                root.after(10, finalize)
        threading.Thread(target=task, daemon=True).start()
    proceed()
    root.mainloop()
