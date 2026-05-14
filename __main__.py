"""
Program Launcher - Entry Point (__main__.py)
Place this file at: programlauncher/__main__.py

This is the entry point when running: python -m programlauncher
"""
import sys
import os

# Add the parent directory to the Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import multiprocessing

def main():
    """Main entry point for the application"""
    # Required for multiprocessing on Windows
    multiprocessing.freeze_support()
    
    # Import here to avoid issues
    from programlauncher.saui import create_launcher_ui
    
    # Launch the UI from saui.py
    create_launcher_ui()


if __name__ == '__main__':
    main()