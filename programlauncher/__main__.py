"""Entry point for python -m programlauncher."""
import multiprocessing


def main():
    """Launch the application UI."""
    multiprocessing.freeze_support()

    from programlauncher.saui import create_launcher_ui

    create_launcher_ui()


if __name__ == "__main__":
    main()
