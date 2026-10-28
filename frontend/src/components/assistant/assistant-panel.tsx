"use client"

import { usePathname } from "next/navigation"
import { useTranslations } from "next-intl"
import { useEffect, useRef, useState } from "react"

import { AssistantHistory } from "@/components/assistant/assistant-history"
import { AssistantMessages } from "@/components/assistant/assistant-messages"
import { PanelResizer } from "@/components/assistant/panel-resizer"
import { PanelHeader } from "@/components/assistant/panel-header"
import { VoiceButton } from "@/components/assistant/voice-button"
import { useAuth } from "@/providers/auth-provider"
import { ChatInput } from "@/components/chat-input"
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog"
import { PHONE_QUERY, TOUCH_QUERY } from "@/config/assistant"
import { MAX_HELP_QUESTION_LENGTH } from "@/config/limits"
import { useAssistantChat } from "@/hooks/use-assistant-chat"
import { useCompanyChoice } from "@/hooks/use-company-choice"
import { useContainedScroll } from "@/hooks/use-contained-scroll"
import { useCurrentPageKey } from "@/hooks/use-page-key"
import { apiFetch } from "@/lib/api"
import { getConfig, getWelcomeStage, pageCompany } from "@/lib/assistant"
import {
  clampPanelWidth,
  savedPanelWidth,
  savePanelWidth,
} from "@/lib/panel-width"
import type { AssistantConfig } from "@/types/assistant"
import type { Company } from "@/types/company"

/** The assistant's panel, kept while the user moves between pages: a drawer at the end side,
 * the whole screen on phones. Signed in, it answers with the user's data about the company
 * picked in its header (the page's company by default, or all companies), keeps a history and
 * takes voice; signed out, it answers about
 * prepza from the FAQ, and the conversation lives only here. */
export function AssistantPanel({
  open,
  onOpenChange,
  onRestored,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  // Whether a recent chat came back after the page loaded.
  onRestored: (recent: boolean) => void
}) {
  const t = useTranslations("assistant")
  const { user } = useAuth()
  const signedIn = user !== null
  const pathname = usePathname()
  const onPage = signedIn ? pageCompany(pathname) : null
  // The history view belongs to the account that opened it.
  const [historyFor, setHistoryFor] = useState<string | null>(null)
  const history = signedIn && historyFor === user.uid

  function setHistory(open: boolean) {
    setHistoryFor(open ? (user?.uid ?? null) : null)
  }
  const [input, setInput] = useState("")
  const [width, setWidth] = useState(savedPanelWidth)
  const [config, setConfig] = useState<AssistantConfig | null>(null)
  const [companies, setCompanies] = useState<Company[]>([])
  const choice = useCompanyChoice(
    onPage,
    companies.map((company) => company.id)
  )
  const chat = useAssistantChat(choice.company, signedIn, onRestored)
  const [stage, setStage] = useState<string | null>(null)
  const scroller = useRef<HTMLDivElement>(null)
  // The panel's element, there only while it's open.
  const [popup, setPopup] = useState<HTMLDivElement | null>(null)
  const field = useRef<HTMLTextAreaElement>(null)
  const onGuidedPage = useCurrentPageKey() !== null

  // Each time it opens: the limits once, and the companies, which may have changed.
  useEffect(() => {
    if (!open || !signedIn) {
      return
    }

    if (!config) {
      getConfig()
        .then(setConfig)
        .catch(() => {})
    }

    apiFetch<Company[]>("/companies/companies?limit=100")
      .then(setCompanies)
      .catch(() => {})
  }, [open, signedIn, config])

  // The welcome's stage, for the company the panel is about, each time it opens empty.
  const welcomeCompany = choice.company
  const empty = chat.messages.length === 0

  useEffect(() => {
    if (!open || !signedIn || !empty) {
      return
    }

    getWelcomeStage(welcomeCompany)
      .then(setStage)
      .catch(() => setStage(null))
  }, [open, signedIn, empty, welcomeCompany])

  useContainedScroll(popup, scroller)

  // Opened, the input is ready to type in.
  useEffect(() => {
    if (open) {
      focusInput()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  // The latest message stays in view as the answer streams.
  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight })
  }, [chat.messages])

  const names = Object.fromEntries(
    companies.map((company) => [company.id, company.name])
  )

  // The input, ready to type in; not on touch screens, where the keyboard would cover the panel.
  function typingFocus() {
    return window.matchMedia(TOUCH_QUERY).matches ? null : field.current
  }

  // At once when the input is there (before what was clicked goes away), else once it's back.
  function focusInput() {
    if (field.current) {
      typingFocus()?.focus()
    } else {
      requestAnimationFrame(() => typingFocus()?.focus())
    }
  }

  function send(text: string, source: "text" | "voice" = "text") {
    setInput("")
    void chat.send(text, source)
  }

  // A link from the panel opens its page; on a phone, where the panel is the whole screen,
  // the panel closes to show it.
  function navigated() {
    if (window.matchMedia(PHONE_QUERY).matches) {
      onOpenChange(false)
    }
  }

  return (
    // Not modal: the page beside it still scrolls, and a click on it closes the panel (but not
    // a click on "ask agent", which toggles it).
    <Dialog
      open={open}
      onOpenChange={(next, details) => {
        const target = details.event?.target

        if (
          details.reason === "outside-press" &&
          target instanceof Element &&
          target.closest("[data-assistant-toggle]")
        ) {
          details.cancel()

          return
        }

        onOpenChange(next)
      }}
      modal={false}
    >
      <DialogContent
        ref={setPopup}
        sheet
        showCloseButton={false}
        style={
          {
            "--sheet-width": `${typeof window === "undefined" ? width : clampPanelWidth(width, window.innerWidth)}px`,
          } as React.CSSProperties
        }
      >
        <PanelResizer
          width={width}
          onResize={(next) => {
            setWidth(next)
            savePanelWidth(next)
          }}
        />
        <DialogTitle className="sr-only">{t("title")}</DialogTitle>
        <PanelHeader
          title={history ? t("history") : t("title")}
          // A picker of the user's companies, signed in and in the chat.
          companies={signedIn && !history ? companies : []}
          company={choice.company}
          onPick={choice.pick}
          history={signedIn ? history : null}
          onHistory={() => setHistory(!history)}
          onNewChat={() => {
            chat.startNew()
            setHistory(false)
            focusInput()
          }}
        />
        <div
          ref={scroller}
          className="flex-1 overflow-y-auto overscroll-contain px-4 pt-4 pb-10"
        >
          {history ? (
            <AssistantHistory
              companyNames={names}
              onOpen={(id) => {
                setHistory(false)
                // The picker follows the conversation's company.
                void chat.open(id).then((company) => {
                  if (company !== undefined) {
                    choice.pick(company)
                  }

                  focusInput()
                })
              }}
              onDeleted={(id) => id === chat.conversationId && chat.startNew()}
            />
          ) : (
            <AssistantMessages
              messages={chat.messages}
              earlier={chat.earlier}
              onEarlier={chat.loadEarlier}
              streaming={chat.streaming}
              signedIn={signedIn}
              stage={signedIn ? stage : "signed_out"}
              onPage={onGuidedPage}
              onAsk={(question) => {
                send(question)
                focusInput()
              }}
              onRetry={chat.retry}
              onVote={(index, value) => void chat.vote(index, value)}
              onNavigate={navigated}
              actions={{
                onConfirm: (id) => void chat.confirm(id),
                onCancel: (id) => void chat.cancel(id),
                busy: chat.streaming,
                companyNames: names,
              }}
            />
          )}
        </div>
        {!history && (
          <div className="shrink-0 px-4 pb-4">
            <ChatInput
              inputRef={field}
              value={input}
              onChange={setInput}
              onSubmit={() => send(input)}
              label={t("title")}
              placeholder={t("placeholder")}
              maxLength={
                signedIn ? config?.max_message_length : MAX_HELP_QUESTION_LENGTH
              }
              streaming={chat.streaming}
              onStop={chat.stop}
              stopLabel={t("stop")}
            >
              {/* Voice goes through the signed-in assistant only. */}
              {signedIn && config && (
                <VoiceButton
                  maxSeconds={config.max_audio_seconds}
                  disabled={chat.streaming}
                  onTranscript={(text) => send(text, "voice")}
                />
              )}
            </ChatInput>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
