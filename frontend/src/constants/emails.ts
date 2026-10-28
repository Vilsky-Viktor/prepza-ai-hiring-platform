// The email settings in the order the Settings page shows them: the activity digest's kinds,
// then the other emails, each with its own note.
export const DIGEST_KINDS = [
  "candidate_finished",
  "invite_undelivered",
  "ats_not_invited",
  "interview_ready",
] as const

export const OTHER_EMAILS = ["reminders", "updates", "promotions"] as const
