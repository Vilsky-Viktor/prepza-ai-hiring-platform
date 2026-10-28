// The home page's "just ask the agent" picture: a chat with the assistant about one interview,
// and the three things it does beside it. Display only.

// The interview the chat is about, its results and the candidate invited to it.
export const ASK_AGENT_INTERVIEW = "Data Analyst"
export const ASK_AGENT_RESULTS = {
  passed: 18,
  total: 42,
  passMark: 70,
  best: 92,
}
export const ASK_AGENT_EMAIL = "anna@example.com"

// The three questions asked, in turn, by their text's key.
export const ASK_AGENT_QUESTIONS = ["stats", "help", "invite"] as const

export type AskAgentQuestion = (typeof ASK_AGENT_QUESTIONS)[number]

// The cards beside the chat, by their text's key.
export const ASK_AGENT_CARDS = ["info", "help", "actions"] as const

export type AskAgentCard = (typeof ASK_AGENT_CARDS)[number]
