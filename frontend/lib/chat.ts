import { humanHeaders } from "@/lib/human-check"
import { ApiError, authHeaders, errorDetail } from "@/lib/api"
import type { AssistantBlock } from "@/types/assistant"
import type { HelpMessage } from "@/types/help"
import type { PageHelpKey } from "@/types/page-help"

/** An error event in a stream: its message, already in the user's language, and its code when
the service gave one (the assistant's "session_expired"). */
export class StreamError extends Error {
  constructor(
    message: string,
    public code?: string
  ) {
    super(message)
  }
}

/** Posts to a streaming route (server-sent events) and calls onEvent with each event's data,
until the stream ends or `signal` aborts. An error event throws a StreamError; a refused request
throws an ApiError. */
export async function streamEvents<T>(
  path: string,
  body: unknown,
  onEvent: (event: T) => void,
  signal: AbortSignal,
  headers: Record<string, string> = {}
) {
  const response = await fetch(`/api${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...headers,
      ...(await authHeaders()),
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!response.ok || !response.body) {
    const detail = errorDetail(await response.json().catch(() => null))

    throw new ApiError(
      response.status,
      detail ?? `Chat failed with status ${response.status}`,
      detail !== null
    )
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ""

  while (true) {
    const { value, done } = await reader.read()

    if (done) {
      return
    }

    // Events end with a blank line; proxies may send CRLF line ends.
    buffer += value.replace(/\r\n?/g, "\n")
    const events = buffer.split("\n\n")
    buffer = events.pop() ?? ""

    for (const event of events) {
      // Only data lines carry the reply; comments (": keep-alive") and other fields don't.
      const lines = event
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart())

      if (lines.length === 0) {
        continue
      }

      const data = JSON.parse(lines.join("\n"))

      if (data.error) {
        throw new StreamError(data.error, data.code)
      }

      onEvent(data)
    }
  }
}

// The help chat's current conversation, so its answers' traces read as one; a new chat gets
// a new id (startHelpChat).
let helpChat = crypto.randomUUID()

/** Starts a new help chat conversation, with its own id. */
export function startHelpChat() {
  helpChat = crypto.randomUUID()
}

/** Asks prepza's help chat (signed-out visitors' assistant); the panel keeps the conversation
and sends it whole, each reply with the signature the chat gave it (the chat reads no reply
without one). Its events: {"delta"}, a {"block"} sign-in card when the visitor asks to sign in,
and {"done"} with the reply's signature. Until the chat has a signed reply, a question shows
the visitor is a person (lib/human-check.ts). `page`: the key of the page the visitor asks on,
whose guide the answer reads. */
export function streamHelp(
  messages: HelpMessage[],
  onEvent: (event: {
    delta?: string
    block?: AssistantBlock
    removed?: boolean
    signature?: string
  }) => void,
  signal: AbortSignal,
  page?: PageHelpKey
) {
  const first = !messages.some(
    (message) => message.role === "assistant" && message.signature
  )

  return humanHeaders(first).then((headers) =>
    streamEvents(
      "/rounds/help/chat",
      { messages, chat_id: helpChat, ...(page && { page }) },
      onEvent,
      signal,
      headers
    )
  )
}
