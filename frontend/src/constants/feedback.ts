// Their wording is in messages/*.json under "reportReasons".
export const REPORT_REASONS = [
  "wrong_answer",
  "unclear",
  "hard_to_read",
  "off_topic",
  "other",
] as const

export const FEEDBACK_HOVER_CLASS =
  "text-muted-foreground transition-colors hover:bg-foreground/10 hover:text-foreground dark:hover:bg-foreground/15"
