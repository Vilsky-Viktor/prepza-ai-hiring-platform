"use client"

import { type Dispatch, type SetStateAction, useEffect, useRef } from "react"

import { useAuth } from "@/components/auth-provider"
import {
  getActiveConversation,
  getConfig,
  withoutSignIn,
} from "@/lib/assistant"
import {
  clearChat,
  newer,
  readChat,
  recentVisitorChat,
  saveChat,
} from "@/lib/assistant-storage"
import type { ChatMessage } from "@/types/assistant"

/** The panel's chat across reloads and sign-ins. On the page's first load, the recent chat
 * comes back (the service says which conversation is; a visitor's, by the window /config
 * gives, also after they signed in, until their first message saves it, unless their own
 * conversation is newer), and `onRestored` hears whether one did. Signing out or another account starts over;
 * a visitor who just signed in keeps their chat on screen. A visitor's chat is kept in the tab
 * with its last message's time. */
export function useChatRestore({
  signedIn,
  streaming,
  messages,
  setMessages,
  open,
  startNew,
  onRestored,
}: {
  signedIn: boolean
  streaming: boolean
  messages: ChatMessage[]
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>
  open: (id: string, quietly: boolean) => Promise<string | null | undefined>
  startNew: () => void
  onRestored: (recent: boolean) => void
}) {
  const { user, loading } = useAuth()
  // Who the panel was restored for: undefined until the page knows, null for a visitor.
  const uid = loading ? undefined : (user?.uid ?? null)
  const restoredFor = useRef<string | null | undefined>(undefined)
  // Whether the first restore has read what a reload kept.
  const lookedAt = useRef(false)

  // Once what a reload kept was looked at, so it isn't overwritten first (also when the panel
  // mounts with the page already known, and React runs its effects twice in development).
  useEffect(() => {
    if (lookedAt.current && !signedIn && !streaming) {
      saveChat(false, { messages, lastAt: new Date().toISOString() })
    }
  }, [signedIn, streaming, messages])

  async function restore(
    before: string | null | undefined,
    now: string | null
  ) {
    if (before) {
      clearChat(true)
      startNew()
    }

    // A visitor who just signed in keeps their chat, without the sign-in cards that did it
    // (on screen, in the tab's copy, and so in what starts their first conversation).
    if (before === null && now) {
      setMessages((current) => {
        const kept = withoutSignIn(current)
        saveChat(false, { messages: kept })

        return kept
      })
    }

    if (before !== undefined) {
      return
    }

    const recent = now ? await restoreConversation() : await restoreVisitor()
    lookedAt.current = true
    onRestored(recent)
  }

  // Signed in: the chat they had as a visitor (until their first message saves it), unless
  // their own recent conversation is newer.
  async function restoreConversation() {
    const [found, visitor] = await Promise.all([
      getActiveConversation().catch(() => null),
      recentVisitor(),
    ])

    if (visitor && !newer(found?.updated_at, visitor.lastAt)) {
      setMessages(withoutSignIn(visitor.messages))

      return true
    }

    return found !== null && (await open(found.id, true)) !== undefined
  }

  async function recentVisitor() {
    const config = await getConfig().catch(() => null)
    const saved = readChat(false)
    const kept = recentVisitorChat(saved, config, Date.now())

    return kept ? { messages: kept, lastAt: saved.lastAt } : null
  }

  async function restoreVisitor() {
    const kept = await recentVisitor()

    if (kept === null) {
      // An old chat is forgotten, not whether the panel is open: it loads when first opened
      // (assistant-provider.tsx), after that was saved.
      const { open } = readChat(false)
      clearChat(false)

      if (open !== undefined) {
        saveChat(false, { open })
      }

      return false
    }

    setMessages(kept.messages)

    return true
  }

  useEffect(() => {
    if (uid === undefined || restoredFor.current === uid) {
      return
    }

    const before = restoredFor.current
    restoredFor.current = uid
    void restore(before, uid)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uid])
}
