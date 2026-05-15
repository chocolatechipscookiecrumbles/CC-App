from . import *
import queue
from .choose_uni import choose_university
from .Folder_Parser import collect_revenue_across_pdfs
from .fill_excel_with_data_revenue import fill_excel_with_data_revenue
from .Excel_Generator import generate_template_excel_revenue
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
    task_store = {}

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

    client_uni = choose_university(unis)
    if client_uni == 1:
        messagebox.showinfo("No uni saved", "No uni saved, exiting program.")
        sys.exit(1)

    if not confirm_preview("Revenue", manifest, client_uni, include_client):
        messagebox.showinfo("Cancelled", "Report generation cancelled.")
        sys.exit(0)

    def proceed():
        summary = WorkflowRunSummary(
            "Revenue",
            folder_path,
            pdfs_found=len(manifest),
            extra={"client": client_uni, "include_client": include_client},
        )
        start_run_log(summary)
        progress_queue = queue.Queue()
        cancel_token = CancellationToken()
        processing_dialog = ProcessingDialog(
            root,
            "Processing Revenue",
            progress_queue,
            cancel_token,
        )
        reporter = ProgressReporter(progress_queue.put)
        task_store["error"] = None

        def task():
            try:
                '''revenue_df = collect_revenue_across_pdfs(folder_path)
                #print(men_sports, women_sports)'''

                revenue_df = collect_revenue_across_pdfs(
                    folder_path,
                    manifest=manifest,
                    summary=summary,
                    progress_reporter=reporter,
                    cancel_token=cancel_token,
                )
                task_store['revenue_df'] = revenue_df
            except Exception as exc:
                task_store["error"] = exc
            finally:
                def finalize():
                    processing_dialog.destroy()

                    if task_store["error"]:
                        summary.finish(cancelled=cancel_token.is_cancelled)
                        log_exception(summary, task_store["error"])
                        messagebox.showerror("Error", f"Revenue processing failed:\n{task_store['error']}")
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

                    ifclient = include_client
                    if ifclient is None:
                        messagebox.showerror("Error", "Nothing selected, exiting program.")
                        sys.exit(1)

                    if summary.processed_count == 0:
                        summary.finish(cancelled=True)
                        messagebox.showerror(
                            "No Revenue Data",
                            "No revenue data was extracted, so no workbook was written.",
                        )
                        show_summary(summary)
                        root.quit()
                        root.destroy()
                        return

                    # Proceed to save file
                    messagebox.showinfo("Save File", "Choose where to save the Excel report.")
                    output_excel = ask_output_path(title="Save Excel File")
                    if not output_excel:
                        messagebox.showinfo("No file saved", "No file saved, exiting program.")
                        summary.finish(cancelled=True)
                        show_summary(summary)
                        root.quit()
                        root.destroy()
                        return
                    reporter.update(
                        current=len(manifest),
                        total=len(manifest),
                        institution=client_uni,
                        stage="Writing workbook",
                        skipped_count=summary.skipped_count,
                    )
                    try:
                        generate_template_excel_revenue(output_excel)
                        fill_excel_with_data_revenue(
                            task_store['revenue_df'],
                            output_excel,
                            client_uni,
                            ifclient,
                            validation_records=summary.extra.get("revenue_validation", []),
                        )
                    except Exception as exc:
                        summary.finish(output_path=output_excel, cancelled=True)
                        log_exception(summary, exc)
                        messagebox.showerror("Error", f"Revenue workbook generation failed:\n{exc}")
                        show_summary(summary)
                        root.quit()
                        root.destroy()
                        return
                    summary.finish(output_path=output_excel)
                    show_summary(summary)
                    messagebox.showinfo("Done", "Excel report generated successfully.")

                    root.quit()
                    root.destroy()

                root.after(10, finalize)
        threading.Thread(target=task, daemon=True).start()
    proceed()
    root.mainloop()
