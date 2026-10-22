// The in-app assistant's API (services/assistant), as the panel reads it; a signed-out
// visitor's answers come from rounds' help chat.
import type { PageHelpKey } from "@/types/page-help"
import type { SignInProvider } from "@/types/sign-in"

/** What the panel shows under an answer for one tool's result: its items, each with the page
 * it opens (null when the service couldn't build one), or for "link" one page; or the sign-in
 * card the help chat sends a visitor who asked to sign in. */
export type AssistantBlock = {
  kind:
    | "candidate_rows"
    | "scorecard_summary"
    | "interview"
    | "credits"
    | "link"
    | "sign_in"
    | "confirm"
  items: Record<string, unknown>[]
  links: (string | null)[]
  // A list's page with all of its items, shown under its rows.
  all?: string | null
  // A link's page (by the service's name for it) and what it opens (an interview's title).
  page?: string | null
  label?: string | null
  // A sign-in card's way to sign in first: the one the visitor asked for.
  provider?: SignInProvider | null
} & Partial<ActionCard>

/** An action the assistant prepared, as its confirmation card shows it: exactly what runs
 * (`preview`), whether it can't be undone, and where it stands. "running" is the panel's own,
 * while a confirm is on its way. */
export type ActionCard = {
  action_id: string
  tool: string
  preview: Record<string, string | number | boolean>
  company_id: string | null
  destructive: boolean
  state: "pending" | "running" | "done" | "failed" | "cancelled"
  // Why it failed, in the user's language.
  detail?: string | null
  // What it's about (a company's name, an interview's title), and what it made.
  subject?: string | null
  result_label?: string | null
  // The company's credits the action would lose (deleting it).
  credits?: { available: number; candidates: number } | null
}

export type ToolProgress = {
  name: string
  state: "running" | "done" | "failed"
  label: string
}

/** One server-sent event of an answer; the error event throws instead (lib/chat.ts). */
export type AssistantEvent = {
  conversation?: { id: string }
  tool?: ToolProgress
  block?: AssistantBlock
  delta?: string
  // The assistant's: the saved answer's id; the help chat's: true, with `answer`.
  done?: { message_id: string } | true
  // The help chat's answer, as a vote on it names it.
  answer?: HelpAnswer
  // A confirmed action's card, in its new state.
  action?: AssistantBlock
  // The user asked to sign out: the panel does it.
  sign_out?: boolean
  // The question had a secret in it: it's removed from the chat.
  removed?: boolean
  // The conversation's new title, for the history.
  title?: string
  // The help chat's signature of its reply, with its last event: sent back with the reply.
  signature?: string
}

export type AssistantMessage = {
  id: string
  role: "user" | "assistant"
  source: "text" | "voice"
  content: string
  blocks: AssistantBlock[]
  status: "complete" | "cancelled" | "failed"
  vote: Vote | null
  created_at: string
}

/** A thumbs up (1) or down (-1) on an answer. */
export type Vote = 1 | -1

/** A help chat answer as a vote on it names it: its id, Langfuse trace and signature. */
export type HelpAnswer = {
  id: string
  trace_id: string | null
  signature: string
}

export type Conversation = {
  id: string
  company_id: string | null
  title: string
  created_at: string
  updated_at: string
}

export type ConversationDetail = Conversation & {
  messages: AssistantMessage[]
  // Earlier messages are left to load (GET .../messages?before=).
  earlier: boolean
}

/** A page of a conversation's earlier messages, oldest first. */
export type MessagesPage = {
  messages: AssistantMessage[]
  earlier: boolean
}

/** The limits the panel keeps to (GET /config). */
export type AssistantConfig = {
  max_message_length: number
  // A chat older than this isn't brought back after a reload.
  restore_minutes: number
  max_audio_seconds: number
  messages_per_hour: number
  messages_per_day: number
}

/** A message as the panel shows it while it's being written, or as it was saved. */
export type ChatMessage = {
  role: "user" | "assistant"
  content: string
  blocks: AssistantBlock[]
  // A question: typed or spoken; removed when it had a secret in it.
  source?: "text" | "voice"
  removed?: boolean
  // A help chat reply's signature, which the next question sends back with it.
  signature?: string
  // An answer's tools so far, by their progress labels.
  progress?: string[]
  // An answer that failed, with what to show and whether a retry can fix it.
  error?: string
  // A written answer, as a vote on it names it: the assistant's saved message, or the help
  // chat's answer; and the vote on it.
  id?: string
  helpAnswer?: HelpAnswer
  vote?: Vote | null
}

// The page a message is asked on (lib/page-context.ts): context for the assistant only.
export type PageContext = {
  key: PageHelpKey
  path: string
  company_id?: string
  interview_id?: string
  candidate_id?: string
  template_id?: string
  practice_round_id?: string
}
