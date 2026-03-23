from __future__ import annotations

import traceback as tb


def blank_exception_details() -> dict[str, str]:
    return {
        "exception_type": "",
        "exception_message": "",
        "traceback": "",
    }


def exception_details(exc: BaseException) -> dict[str, str]:
    return {
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "traceback": "".join(tb.format_exception(type(exc), exc, exc.__traceback__)).strip(),
    }
