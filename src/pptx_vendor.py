from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def ensure_pptx_vendor() -> None:
    if importlib.util.find_spec("pptx") is not None:
        return

    vendor_root = Path(__file__).resolve().parent / "_vendor_pptx"
    vendor_dirs = [
        "typing_extensions-4.15.0-py3-none-any",
        "xlsxwriter-3.2.9-py3-none-any",
        "lxml-6.1.0-cp312-cp312-win_amd64",
        "python_pptx-1.0.2-py3-none-any",
    ]
    for dirname in vendor_dirs:
        candidate = vendor_root / dirname
        if candidate.exists():
            sys.path.insert(0, str(candidate))
