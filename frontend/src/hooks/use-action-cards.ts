"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"

import { ApiError, apiErrorMessage } from "@/lib/api"
import {
  cancelAction,
  confirmAction,
  refreshToken,
  withCard,
} from "@/lib/assistant"
import type {
  AssistantBlock,
  AssistantEvent,
  ChatMessage,
} from "@/types/assistant"

/** The action cards' buttons. Confirm runs the action on the service, which streams the card's
 * new state and the assistant's words about it as a new answer (`streamAnswer`); a refused
 * token is refreshed and the confirm sent again, once. Cancel drops it. A card the service
 * can't run any more (expired, handled elsewhere) shows why. */
export function useActionCards({
  conversationId,
  messages,
  setMessages,
  streamAnswer,
}: {
  conversationId: string | null
  messages: ChatMessage[]
  setMessages: (change: (current: ChatMessage[]) => ChatMessage[]) => void
  streamAnswer: (
    shown: ChatMessage[],
    start: (
      onEvent: (event: AssistantEvent) => void,
      signal: AbortSignal
    ) => Promise<void>
  ) => Promise<unknown>
}) {
  const t = useTranslations("assistant")
  const router = useRouter()

  function updateCard(actionId: string, change: Partial<AssistantBlock>) {
    setMessages((current) => withCard(current, actionId, change))
  }

  async function confirm(actionId: string, resent = false): Promise<void> {
    if (!conversationId) {
      return
    }

    const before = withCard(messages, actionId, { state: "running" })
    const answer: ChatMessage = { role: "assistant", content: "", blocks: [] }
    const error = await streamAnswer([...before, answer], (handle, signal) =>
      confirmAction(conversationId, actionId, handle, signal)
    )

    // The page beside the panel shows what changed (a new company in the list).
    if (!error) {
      router.refresh()
    }

    if (error instanceof ApiError && error.status === 401 && !resent) {
      await refreshToken()

      return confirm(actionId, true)
    }

    if (error) {
      setMessages((current) =>
        withCard(current.slice(0, -1), actionId, {
          state: "failed",
          detail: apiErrorMessage(error, t("failed")),
        })
      )
    }
  }

  async function cancel(actionId: string) {
    if (!conversationId) {
      return
    }

    try {
      updateCard(actionId, await cancelAction(conversationId, actionId))
    } catch (error) {
      updateCard(actionId, {
        state: "failed",
        detail: apiErrorMessage(error, t("failed")),
      })
    }
  }

  return { confirm, cancel }
}
