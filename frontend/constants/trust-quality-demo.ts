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

// Light through the loop's net: each ring's seconds from the chip to the ellipse, and how many
// rings run at once, evenly apart.
export const NET_WAVE_SECONDS = 8
export const NET_WAVES = 2

// The ellipse the steps sit on, centred on the stage: its radii, in percent of the stage's width
// and height. The steps sit evenly round it, the first at the top, then clockwise, so left and
// right mirror each other.
export const QUALITY_ELLIPSE = { x: 36, y: 34 }

// A step card's padding and border from laptops up, top and bottom together, in pixels (pt-9
// under the icon on its edge, pb-5, border).
export const QUALITY_CARD_PADDING = 58

// The net's mesh, in pixels.
export const NET_CELL = 22

// How long the question rests on a step before it moves on, in milliseconds.
export const QUALITY_PAUSE_MS = 900

// The cards under the loop, by their text's key.
export const TRUST_CARDS = ["person", "fair", "laws", "log"] as const

export type TrustCard = (typeof TRUST_CARDS)[number]

// The question travelling the loop, this many times the usual traveller's size.
export const QUESTION_SIZE = 2.6
