from __future__ import annotations

STATUS_NOT_STARTED = "not_started"
STATUS_SKIPPED_EXISTING = "skipped_existing"
STATUS_COMPLETED = "completed"
STATUS_BLOCKED_MISSING_CREDENTIALS = "blocked_missing_credentials"
STATUS_FAILED = "failed"

SUCCESS_STATUSES = {STATUS_COMPLETED, STATUS_SKIPPED_EXISTING}


def is_success_status(status: str | None) -> bool:
    return (status or "").strip().lower() in SUCCESS_STATUSES
