import { SAVED_CHAT_KEY, SAVED_VISITOR_CHAT_KEY } from "@/constants/assistant"
import type { AssistantConfig, ChatMessage } from "@/types/assistant"

/** The panel as it was before a reload: open or not, the company picked (signed in), and the
 * visitor's messages with their last one's time (signed out). Signed in, the service knows
 * the conversation to bring back. */
export type SavedChat = {
  open?: boolean
  messages?: ChatMessage[]
  lastAt?: string
  // The company picked in the panel (null: all companies), on the page's company it was picked
  // on (null: a page without one).
  choice?: { page: string | null; company: string | null }
}

function store(signedIn: boolean) {
  return signedIn ? localStorage : sessionStorage
}

function key(signedIn: boolean) {
  return signedIn ? SAVED_CHAT_KEY : SAVED_VISITOR_CHAT_KEY
}

/** The saved panel for the signed-in user or the visitor; empty when there's none, it doesn't
 * read right, or storage is blocked (a private window). */
export function readChat(signedIn: boolean): SavedChat {
  try {
    const value = JSON.parse(store(signedIn).getItem(key(signedIn)) ?? "null")

    return value && typeof value === "object" && !Array.isArray(value)
      ? value
      : {}
  } catch {
    return {}
  }
}

/** Keeps `change` on top of what's saved; nothing happens when storage is blocked. */
export function saveChat(signedIn: boolean, change: SavedChat) {
  try {
    const next = { ...readChat(signedIn), ...change }
    store(signedIn).setItem(key(signedIn), JSON.stringify(next))
  } catch {
    // The panel simply isn't restored.
  }
}

/** Forgets the visitor's chat, or both (signing out). */
export function clearChat(both: boolean) {
  for (const signedIn of both ? [true, false] : [false]) {
    try {
      store(signedIn).removeItem(key(signedIn))
    } catch {
      // Nothing was kept.
    }
  }
}

/** Whether the panel was open before the reload: signed in, or as the visitor who was signing
 * in. */
export function wasOpen(signedIn: boolean) {
  return Boolean(readChat(false).open || (signedIn && readChat(true).open))
}

/** The visitor's kept messages when their last one is within the service's window (`config`'s
 * restore_minutes) of `now`; null when there are none, they're older, or the window is
 * unknown. */
export function recentVisitorChat(
  saved: SavedChat,
  config: AssistantConfig | null,
  now: number
): ChatMessage[] | null {
  const age = now - Date.parse(saved.lastAt ?? "")
  const recent = config !== null && age <= config.restore_minutes * 60_000

  return recent && Array.isArray(saved.messages) && saved.messages.length > 0
    ? saved.messages
    : null
}

/** Whether the time `a` is after `b` (ISO dates; a missing one is never after). */
export function newer(
  a: string | undefined | null,
  b: string | undefined | null
) {
  return Boolean(a) && Date.parse(a!) > Date.parse(b ?? "")
}
