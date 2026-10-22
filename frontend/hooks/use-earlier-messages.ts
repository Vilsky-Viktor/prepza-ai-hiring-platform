"use client"

import { useTranslations } from "next-intl"
import { useRef, useState, type Dispatch, type SetStateAction } from "react"
import { toast } from "sonner"

import { apiErrorMessage } from "@/lib/api"
import { getEarlierMessages, shownMessage } from "@/lib/assistant"
import type { ChatMessage } from "@/types/assistant"

/** An opened conversation shows its latest messages; `loadEarlier` puts the page before them on
 * top, while `earlier` says more are left. */
export function useEarlierMessages(
  conversationId: string | null,
  messages: ChatMessage[],
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>
) {
  const t = useTranslations("assistant")
  const [earlier, setEarlier] = useState(false)
  const loading = useRef(false)

  async function loadEarlier() {
    const first = messages.find((message) => message.id)?.id

    if (!conversationId || !first || loading.current) {
      return
    }

    loading.current = true

    try {
      const page = await getEarlierMessages(conversationId, first)
      setMessages((current) => [...page.messages.map(shownMessage), ...current])
      setEarlier(page.earlier)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("openFailed")))
    } finally {
      loading.current = false
    }
  }

  return { earlier, setEarlier, loadEarlier }
}
