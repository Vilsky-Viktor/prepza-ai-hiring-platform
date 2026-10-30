// The home page's "everything is free" section: the receipt that prints as it comes into view.
// Display only: the counts are a made-up interview's, the prices come from billing's catalog.

import type { DemoStep } from "@/hooks/use-demo-steps"

// The receipt's free lines, in order, by their text's key; each costs nothing.
export const FREE_LINES = [
  "create",
  "review",
  "invite",
  "reports",
  "connect",
] as const

// The made-up interview's invited candidates; as many answer as the biggest top-up pays for.
export const DEMO_INVITED = 500

// Blank until seen, then the free lines tick in one by one, a pause, and the paid line lands;
// the receipt then stays finished until it's scrolled back into view.
export const RECEIPT_STEPS: DemoStep[] = [
  { name: "blank", ms: 400 },
  { name: "free", ms: 280, repeat: FREE_LINES.length },
  { name: "pause", ms: 900 },
  { name: "paid", ms: 86_400_000 },
]

// The small print under the prices, by its text's key.
export const NOTES = ["subscription", "unanswered", "expire", "refund"] as const
