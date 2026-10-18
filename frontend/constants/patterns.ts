// The statuses the patterns tab lists, as generation names them; the first is its default.
export const PATTERN_STATUSES = [
  "proposed",
  "approved",
  "in_use",
  "dismissed",
] as const

export type PatternStatus = (typeof PATTERN_STATUSES)[number]
