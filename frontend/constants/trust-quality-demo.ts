// The home page's "trust, quality and compliance" section: the quality loop's steps and the
// cards under it. Display only.

// The loop's steps, in order, by their text's key; after the last, back to the first.
export const QUALITY_STEPS = [
  "generated",
  "checked",
  "answered",
  "flagged",
  "rewritten",
] as const

export type QualityStep = (typeof QUALITY_STEPS)[number]

// The ellipse the steps sit on, centred on the stage: its radii, in percent of the stage's width
// and height. The steps sit evenly round it, the first at the top, then clockwise, so left and
// right mirror each other.
export const QUALITY_ELLIPSE = { x: 36, y: 34 }

// How long the question rests on a step before it moves on, in milliseconds.
export const QUALITY_PAUSE_MS = 900

// The cards under the loop, by their text's key.
export const TRUST_CARDS = ["person", "fair", "laws", "log"] as const

export type TrustCard = (typeof TRUST_CARDS)[number]

// The question travelling the loop, this many times the usual traveller's size.
export const QUESTION_SIZE = 1.9
