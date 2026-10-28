from enum import StrEnum


class Status(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Nothing changes a generation once it's here.
FINISHED = (Status.DONE, Status.CANCELLED)
