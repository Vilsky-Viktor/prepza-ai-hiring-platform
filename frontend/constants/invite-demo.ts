// The home page's "invite candidates from everywhere" picture: the interview candidates come
// into, and the ways they come, each a card around it with a wire to it. Display only.

export const DEMO_INVITE_INTERVIEW = {
  title: "B2B Account Executive",
  topics: 5,
  questions: 350,
}

// Each way: its text's key, where its card sits from laptops up (`x` from the stage's start
// edge, or its end edge on the `end` side, and `y` from the top, in percent; the rest of the
// stage keeps the interview's middle free), when its spark first runs, in seconds, and how its
// card floats: one sway's length in seconds, and how far into it the card starts, so no two
// float together. The middle ones sit further out, so no card is in another's wire's way. On
// phones half are above the interview and half below, in this order.
export const INVITE_SOURCES = [
  { key: "ats", side: "start", x: 9, y: 8, delay: 0, sway: 7, phase: 0 },
  { key: "email", side: "start", x: 1, y: 33, delay: 1.4, sway: 6, phase: 2 },
  { key: "file", side: "start", x: 4, y: 58, delay: 0.6, sway: 8, phase: 5 },
  { key: "link", side: "start", x: 13, y: 83, delay: 2.1, sway: 6.5, phase: 1 },
  { key: "api", side: "end", x: 13, y: 9, delay: 0.9, sway: 7.5, phase: 3 },
  { key: "sdk", side: "end", x: 3, y: 34, delay: 2.4, sway: 6, phase: 4 },
  { key: "agent", side: "end", x: 1, y: 59, delay: 0.3, sway: 8.5, phase: 2.5 },
  { key: "apps", side: "end", x: 11, y: 84, delay: 1.8, sway: 7, phase: 6 },
] as const

export type InviteSource = (typeof INVITE_SOURCES)[number]

// The distance between two wires where they meet the interview's card, in pixels.
export const INVITE_WIRE_GAP = 18

// How far into a card its wire starts, in pixels, so the card's float never shows its end.
export const INVITE_WIRE_INSET = 14

// How many ATS logos fit a phone's or tablet's narrow card, beside each other in its tile;
// laptops show them all.
export const PHONE_ATS_LOGOS = 2

// The interview's candidates: the count it starts from, how many arrive before it starts again
// from there, and the initials of those who arrive, in turn; the card shows the latest few.
export const DEMO_INVITE_CANDIDATES = {
  from: 124,
  arrivals: 40,
  initials: ["AK", "MS", "JL", "PR", "TN", "EW", "DO", "LC", "RB", "SV"],
  shown: 4,
}

// How fast candidates run along the wires to the interview, in pixels a second: a little slower
// than the hero's.
export const INVITE_SPEED = 105

// The bell's speed from the interview to Slack, pixels a second: slower than the candidates,
// since its wire is short and at their speed the bell only flashes past; and when it first runs.
export const INVITE_NOTIFY_SPEED = 40
export const INVITE_NOTIFY_DELAY = 0.9
