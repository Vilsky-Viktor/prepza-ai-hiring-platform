"use client"

import { useParams, usePathname } from "next/navigation"
import { useTranslations } from "next-intl"
import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { apiErrorMessage } from "@/lib/api"
import {
  getConversation,
  helpConversation,
  withoutSecret,
  refreshToken,
  streamAssistant,
  voteAnswer,
  withCard,
  withEvent,
} from "@/lib/assistant"
import { clearChat } from "@/lib/assistant-storage"
import { signOut } from "@/lib/auth"
import { StreamError, streamHelp } from "@/lib/chat"
import { pageContext } from "@/lib/page-context"
import { pageKey } from "@/lib/page-key"
import { useActionCards } from "@/hooks/use-action-cards"
import { useChatRestore } from "@/hooks/use-chat-restore"
import type { AssistantEvent, ChatMessage, Vote } from "@/types/assistant"

// The service's error code for a token it stopped taking mid-answer.
const SESSION_EXPIRED = "session_expired"

/** The assistant's conversation in the panel: its messages, the answer streaming into the last
 * one. Each message goes with the company picked in the panel (`company`; null: all of them)
 * and the page it's asked on (its guide's key, path and ids; signed out, the key only).
 * Signed out, the FAQ's help chat answers instead: the conversation lives only here (and in the
 * tab's sessionStorage). A reload brings back a recent chat; a visitor who signs in keeps their
 * chat, which the first message then saves as the start of a conversation. Actions the
 * assistant prepares run when the user confirms their cards. */
export function useAssistantChat(
  company: string | null,
  signedIn: boolean,
  onRestored: (recent: boolean) => void
) {
  const t = useTranslations("assistant")
  const pathname = usePathname()
  const params = useParams()
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const stream = useRef<AbortController | null>(null)

  useEffect(() => () => stream.current?.abort(), [])

  const { confirm, cancel } = useActionCards({
    conversationId,
    messages,
    setMessages,
    streamAnswer,
  })

  useChatRestore({
    signedIn,
    streaming,
    messages,
    setMessages,
    open,
    startNew,
    onRestored,
  })

  // The answer being written is always the last message.
  function updateAnswer(change: (answer: ChatMessage) => ChatMessage) {
    setMessages((current) => [...current.slice(0, -1), change(current.at(-1)!)])
  }

  function apply(event: AssistantEvent) {
    // The question had a secret in it: the service kept nothing of it, and neither does the
    // panel (nor what it keeps for a reload).
    if (event.removed) {
      setMessages((current) => withoutSecret(current))
    }

    updateAnswer((answer) => withEvent(answer, event))
  }

  /** The user's vote on the answer at `index` (null: cleared), shown at once and put back as it
   * was if it couldn't be saved. */
  async function vote(index: number, value: Vote | null) {
    const answer = messages[index]
    const setVote = (next: Vote | null | undefined) =>
      setMessages((current) =>
        current.map((message, at) =>
          at === index ? { ...message, vote: next } : message
        )
      )

    setVote(value)

    try {
      await voteAnswer(conversationId, answer, value)
    } catch (error) {
      setVote(answer.vote)
      toast.error(apiErrorMessage(error, t("voteFailed")))
    }
  }

  function onEvent(event: AssistantEvent) {
    if (event.conversation) {
      setConversationId(event.conversation.id)
      clearChat(false)
    }

    if (event.action?.action_id) {
      setMessages((current) =>
        withCard(current, event.action!.action_id!, event.action!)
      )
    }

    // The user asked to sign out: done at once, and the panel shows the visitor's welcome.
    if (event.sign_out) {
      void signOut()
    }

    apply(event)
  }

  /** Shows `shown` (ending with the answer to write) and streams into its last message; the
   * error, if the stream failed (not when the user stopped it). */
  async function streamAnswer(
    shown: ChatMessage[],
    start: (
      onEvent: (event: AssistantEvent) => void,
      signal: AbortSignal
    ) => Promise<void>
  ) {
    setMessages(shown)
    setStreaming(true)
    stream.current = new AbortController()
    const { signal } = stream.current
    let failure: unknown = null

    try {
      await start(onEvent, signal)
    } catch (error) {
      failure = signal.aborted ? null : error
    }

    setStreaming(false)

    return failure
  }

  function showError(error: unknown) {
    const message =
      error instanceof StreamError
        ? error.message
        : apiErrorMessage(error, t("failed"))
    updateAnswer((current) => ({ ...current, error: message }))
  }

  /** Asks `text`, after `earlier` (the conversation without a failed attempt). A token the
   * service stopped taking is refreshed and the message sent again, once. */
  async function ask(
    text: string,
    source: "text" | "voice",
    earlier: ChatMessage[],
    conversation: string | null,
    resent = false
  ) {
    const question: ChatMessage = {
      role: "user",
      content: text,
      blocks: [],
      source,
    }
    const answer: ChatMessage = { role: "assistant", content: "", blocks: [] }
    const page = pageContext(pageKey(), params, pathname)
    const error = await streamAnswer(
      [...earlier, question, answer],
      (handle, signal) =>
        signedIn
          ? streamAssistant(
              {
                message: text,
                source,
                ...(page && { page }),
                ...(company && { company_id: company }),
                // A new conversation starts with what the user asked before signing in.
                ...(conversation
                  ? { conversation_id: conversation }
                  : { earlier: helpConversation(earlier) }),
              },
              handle,
              signal
            )
          : streamHelp(
              helpConversation([...earlier, question]),
              handle,
              signal,
              page?.key
            )
    )

    if (
      error instanceof StreamError &&
      error.code === SESSION_EXPIRED &&
      !resent
    ) {
      await refreshToken()

      return ask(text, source, earlier, conversationId ?? conversation, true)
    }

    if (error) {
      showError(error)
    }
  }

  function send(text: string, source: "text" | "voice" = "text") {
    return ask(text.trim(), source, messages, conversationId)
  }

  /** Asks the last question again, in place of its failed answer. */
  function retry() {
    const question = messages.at(-2)

    if (question) {
      const earlier = messages.slice(0, -2)
      void ask(
        question.content,
        question.source ?? "text",
        earlier,
        conversationId
      )
    }
  }

  function stop() {
    stream.current?.abort()
  }

  function startNew() {
    stop()
    setConversationId(null)
    setMessages([])
    clearChat(false)
  }

  /** Opens one of the user's conversations, and gives its company (undefined when it couldn't);
   * `quietly` (restoring after a reload), one that's gone leaves the welcome without an
   * error. */
  async function open(
    id: string,
    quietly = false
  ): Promise<string | null | undefined> {
    stop()

    try {
      const found = await getConversation(id)
      setConversationId(found.id)
      setMessages(
        found.messages.map((message) => ({
          role: message.role,
          content: message.content,
          blocks: message.blocks,
          source: message.source,
          id: message.id,
          vote: message.vote,
        }))
      )
      return found.company_id
    } catch (error) {
      if (!quietly) {
        toast.error(apiErrorMessage(error, t("openFailed")))
      }

      return undefined
    }
  }

  return {
    conversationId,
    started: conversationId !== null || messages.length > 0,
    messages,
    streaming,
    send,
    retry,
    vote,
    confirm,
    cancel,
    stop,
    startNew,
    open,
  }
}
