import { COMPANY_PATH, LINK_PAGES } from "@/constants/assistant"
import { ApiError, apiFetch, authHeaders, errorDetail } from "@/lib/api"
import { streamEvents } from "@/lib/chat"
import { firebaseAuth } from "@/lib/firebase"
import type {
  AssistantBlock,
  AssistantMessage,
  ChatMessage,
  AssistantConfig,
  AssistantEvent,
  Conversation,
  ConversationDetail,
  MessagesPage,
  PageContext,
  Vote,
} from "@/types/assistant"
import type { HelpMessage } from "@/types/help"

const BASE = "/assistant"

/** Sends a message to the assistant and calls onEvent with each event of its answer. */
export function streamAssistant(
  body: {
    message: string
    conversation_id?: string
    company_id?: string
    source?: "text" | "voice"
    page?: PageContext
    earlier?: { role: "user" | "assistant"; content: string }[]
  },
  onEvent: (event: AssistantEvent) => void,
  signal: AbortSignal
) {
  return streamEvents<AssistantEvent>(`${BASE}/chat`, body, onEvent, signal)
}

export function getConfig() {
  return apiFetch<AssistantConfig>(`${BASE}/config`)
}

/** The user's stage for the welcome, about the page's company or all of theirs. */
export async function getWelcomeStage(companyId: string | null) {
  const query = companyId ? `?company_id=${companyId}` : ""

  return (await apiFetch<{ stage: string }>(`${BASE}/welcome${query}`)).stage
}

/** The conversation to bring back after a reload: the user's latest, if it's recent (the
 * service decides); null when there's none. */
export async function getActiveConversation() {
  const found = await apiFetch<Conversation | undefined>(
    `${BASE}/conversations/active`
  )

  return found ?? null
}

/** Runs an action the user confirmed: its card's new state ({"action"}), then the assistant's
 * words about it, streamed like an answer. */
export function confirmAction(
  conversationId: string,
  actionId: string,
  onEvent: (event: AssistantEvent) => void,
  signal: AbortSignal
) {
  const path = `${BASE}/conversations/${conversationId}/actions/${actionId}/confirm`

  return streamEvents<AssistantEvent>(path, {}, onEvent, signal)
}

export function cancelAction(conversationId: string, actionId: string) {
  return apiFetch<{ action_id: string; state: "cancelled" }>(
    `${BASE}/conversations/${conversationId}/actions/${actionId}/cancel`,
    { method: "POST" }
  )
}

export function listConversations() {
  return apiFetch<Conversation[]>(`${BASE}/conversations`)
}

export function getConversation(id: string) {
  return apiFetch<ConversationDetail>(`${BASE}/conversations/${id}`)
}

/** The page of messages before the message `before` (the earliest shown). */
export function getEarlierMessages(id: string, before: string) {
  return apiFetch<MessagesPage>(
    `${BASE}/conversations/${id}/messages?before=${before}`
  )
}

/** A stored message, as the panel shows it. */
export function shownMessage(message: AssistantMessage): ChatMessage {
  return {
    role: message.role,
    content: message.content,
    blocks: message.blocks,
    source: message.source,
    id: message.id,
    vote: message.vote,
  }
}

export function deleteConversation(id: string) {
  return apiFetch<void>(`${BASE}/conversations/${id}`, { method: "DELETE" })
}

/** A voice message's text, heard in the interface's language. The recording is the body. */
export async function transcribe(audio: Blob): Promise<string> {
  const response = await fetch(`/api${BASE}/transcribe`, {
    method: "POST",
    headers: { ...(await authHeaders()), "Content-Type": audio.type },
    body: audio,
  })
  const body = await response.json().catch(() => null)

  if (!response.ok) {
    const detail = errorDetail(body)

    throw new ApiError(
      response.status,
      detail ?? `Transcription failed with status ${response.status}`,
      detail !== null
    )
  }

  return body.text
}

/** An answer's link, only to one of the app's own pages ("/…", never "//host" or a scheme);
 * null for anything else. */
export function inAppHref(href: unknown): string | null {
  if (
    typeof href !== "string" ||
    !href.startsWith("/") ||
    href.startsWith("//")
  ) {
    return null
  }

  return href.includes("\\") ? null : href
}

/** A link in an answer's text, only to a page the panel knows (linkPage), by its path alone:
 * text the model read (a candidate's answer, a job description) could steer it into writing
 * others, such as an AI app's approval (/connect?request=…) or a redirect (?next=…). Null for
 * anything else. */
export function answerHref(href: unknown): string | null {
  const inApp = inAppHref(href)

  if (!inApp) {
    return null
  }

  const path = inApp.split(/[?#]/)[0]

  return linkPage(path) ? path : null
}

/** The "assistant.pages" message naming the page a link opens, or null for a page the panel
 * doesn't know. */
export function linkPage(href: string): string | null {
  return LINK_PAGES.find(([pattern]) => pattern.test(href))?.[1] ?? null
}

/** An answer's blocks as the panel shows them: rows of items, each with its page, and the pages
 * the "link" blocks lead to once each, after the rows. */
export function answerParts(blocks: AssistantBlock[]) {
  const rows = blocks
    .filter((block) => !["link", "sign_in", "confirm"].includes(block.kind))
    .map((block) => ({
      kind: block.kind,
      items: block.items.map((item, index) => ({
        item,
        href: inAppHref(block.links[index]),
      })),
      all: inAppHref(block.all ?? null),
    }))
  // The answer's link (the service sends one at most): where it goes and what names it.
  const links = blocks
    .filter((block) => block.kind === "link")
    .flatMap((block) =>
      block.links.map((href) => ({
        href: inAppHref(href),
        label: block.label ?? null,
        page: block.page ?? null,
      }))
    )
    .filter(
      (
        found
      ): found is { href: string; label: string | null; page: string | null } =>
        found.href !== null
    )

  const signIn = blocks.find((block) => block.kind === "sign_in")
  const cards = blocks.filter((block) => block.kind === "confirm")

  return { rows, links, signIn, cards }
}

/** The company a page is about (/companies/<id>/…), or null. */
export function pageCompany(path: string): string | null {
  return COMPANY_PATH.exec(path)?.[1] ?? null
}

/** The conversation as the help chat reads it: the questions and the answers that came. */
export function helpConversation(messages: ChatMessage[]): HelpMessage[] {
  return messages
    .filter((message) => message.content && !message.error)
    .map(({ role, content, signature }) => ({
      role,
      content,
      // A help chat reply goes with its signature, or the chat doesn't read it.
      ...(signature && { signature }),
    }))
}

/** `messages` with one action card's fields changed, wherever it is. */
export function withCard(
  messages: ChatMessage[],
  actionId: string,
  change: Partial<AssistantBlock>
): ChatMessage[] {
  return messages.map((message) => ({
    ...message,
    blocks: message.blocks.map((block) =>
      block.action_id === actionId ? { ...block, ...change } : block
    ),
  }))
}

/** A fresh token for the next call, after a service refused the one it had. */
export async function refreshToken() {
  await (await firebaseAuth()).currentUser?.getIdToken(true)
}

/** The chat without its sign-in cards, once the visitor has signed in. */
export function withoutSignIn(messages: ChatMessage[]): ChatMessage[] {
  return messages.map((message) => ({
    ...message,
    blocks: message.blocks.filter((block) => block.kind !== "sign_in"),
  }))
}

/** The chat with the question before the answer being written (the last message) emptied and
 * marked removed: it had a secret in it. */
export function withoutSecret(messages: ChatMessage[]): ChatMessage[] {
  const question = messages.length - 2

  return messages.map((message, index) =>
    index === question ? { ...message, content: "", removed: true } : message
  )
}

/** The answer being written with one event of it applied: a tool at work, a block, more text,
 * the help chat's signature, and once it's done, what a vote on it names. */
export function withEvent(
  answer: ChatMessage,
  event: AssistantEvent
): ChatMessage {
  const { tool, block, delta, signature, done } = event

  return {
    ...answer,
    ...(tool && {
      progress: [...new Set([...(answer.progress ?? []), tool.label])],
    }),
    ...(block && { blocks: [...answer.blocks, block] }),
    ...(delta && { content: answer.content + delta }),
    ...(signature && { signature }),
    ...(done && done !== true && { id: done.message_id }),
    ...(event.answer && { helpAnswer: event.answer }),
  }
}

/** Saves the user's vote on an answer (null clears it): the assistant's in its conversation,
 * the help chat's with the answer's signature. */
export function voteAnswer(
  conversationId: string | null,
  answer: ChatMessage,
  value: Vote | null
) {
  const help = answer.helpAnswer
  const [path, body] = help
    ? [
        `/rounds/help/answers/${help.id}/vote`,
        { trace_id: help.trace_id, signature: help.signature, value },
      ]
    : [
        `${BASE}/conversations/${conversationId}/messages/${answer.id}/vote`,
        { value },
      ]

  return apiFetch(path, { method: "PUT", body: JSON.stringify(body) })
}
