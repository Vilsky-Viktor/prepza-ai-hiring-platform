// The home page's "automate your hiring" picture: the ways other tools work with prepza, each a
// card wired to the prepza card, and Slack after it. Display only.

// The cards around prepza, by their text's key.
export const AUTOMATE_CARDS = [
  "platform",
  "api",
  "sdk",
  "webhook",
  "aiApp",
  "mcp",
  "jobBoard",
  "link",
  "slack",
] as const

export type AutomateCard = (typeof AUTOMATE_CARDS)[number]

// When each wire's traveller first runs, in seconds, so no two set off together.
export const AUTOMATE_DELAYS = {
  request: 0,
  apiIn: 0.8,
  embed: 2.9,
  sdkIn: 0.5,
  webhookOut: 1.6,
  event: 2.3,
  ask: 0.4,
  answer: 1.9,
  mcpAsk: 1.2,
  mcpAnswer: 2.6,
  apply: 0.2,
  linkIn: 1.5,
  notify: 0.9,
}

// The distance between two wires where they meet the prepza card, and between a pair of wires
// side by side (the AI app's and the MCP server's), in pixels.
// The bell's speed to Slack, pixels a second: slower than the others, since its wire is short
// and at their speed the bell only flashes past.
export const AUTOMATE_NOTIFY_SPEED = 40

export const AUTOMATE_WIRE_GAP = 16

// How far into a card its wire starts, in pixels.
export const AUTOMATE_WIRE_INSET = 10
