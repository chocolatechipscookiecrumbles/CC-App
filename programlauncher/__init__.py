"""
Compatibility package for running the source tree from the repository root.

The application modules currently live at the repo root. Extending this
package path lets imports such as programlauncher.common resolve those modules
without requiring the checkout directory itself to be named programlauncher.
"""
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
_ROOT = Path(__file__).resolve().parent.parent
__path__ = [str(_PACKAGE_DIR), str(_ROOT)]

__version__ = "1.0.0"
__author__ = "DW"

__all__ = []
