"use client"

import dynamic from "next/dynamic"
import {
  createContext,
  useContext,
  useState,
  useSyncExternalStore,
} from "react"

import { useAuth } from "@/providers/auth-provider"
import { saveChat, wasOpen } from "@/lib/assistant-storage"

// The panel and all it brings (markdown, voice, actions) load the first time it's needed, not
// with every page: public pages, invites and the interview itself never ship it unopened.
const AssistantPanel = dynamic(
  () =>
    import("@/features/assistant/components/assistant-panel").then(
      (module) => module.AssistantPanel
    ),
  { ssr: false }
)

// Opens or closes the assistant's panel.
const AssistantContext = createContext<() => void>(() => {})

/** The assistant's panel, mounted once it's first opened (or right away when it was open before
 * a reload, to bring the chat back), then for every page, so its conversation survives moving
 * between them; the header's button toggles it. */
export function AssistantProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  const [opened, setOpened] = useState(false)
  const { user } = useAuth()
  const signedIn = user !== null
  // Open before a reload: loaded at once, to bring the chat back. Not known on the server.
  const wasOpenBefore = useSyncExternalStore(
    noChanges,
    () => wasOpen(signedIn),
    () => false
  )
  const needed = opened || wasOpenBefore

  function change(next: boolean) {
    setOpened(true)
    setOpen(next)
    saveChat(signedIn, { open: next })

    // The visitor's chat is part of this one now.
    if (signedIn) {
      saveChat(false, { open: next })
    }
  }

  return (
    <AssistantContext value={() => change(!open)}>
      {children}
      {needed && (
        <AssistantPanel
          open={open}
          onOpenChange={change}
          // Open again after a reload when it was open, and only with a recent chat.
          onRestored={(recent) => recent && wasOpen(signedIn) && setOpen(true)}
        />
      )}
    </AssistantContext>
  )
}

// The stored chat changes only through this provider, which renders again then.
function noChanges() {
  return () => {}
}

/** Opens the assistant's panel, or closes it when open. */
export function useAssistant() {
  return useContext(AssistantContext)
}
