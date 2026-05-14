from programlauncher.common.report_log import write_report as _write_report


def write_report(folder_path, items):
    _write_report(folder_path, items, workflow="TOE")
