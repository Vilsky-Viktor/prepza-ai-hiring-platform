from enum import StrEnum


class ReportReason(StrEnum):
    WRONG_ANSWER = "wrong_answer"
    UNCLEAR = "unclear"
    HARD_TO_READ = "hard_to_read"
    OFF_TOPIC = "off_topic"
    OTHER = "other"


class ReportStatus(StrEnum):
    OPEN = "open"


MAX_REPORT_COMMENT_LENGTH = 1000
