"use client"

import { useTranslations } from "next-intl"

import { AnswerBlocks } from "@/components/assistant/answer-blocks"
import { type CardActions } from "@/components/assistant/action-card"
import { AnswerMarkdown } from "@/components/assistant/answer-markdown"
import { AnswerVote } from "@/components/assistant/answer-vote"
import { ChatBubble, ThinkingDots } from "@/components/chat-bubble"
import { Button } from "@/components/ui/button"
import { WELCOME_QUESTIONS } from "@/constants/assistant"
import type { ChatMessage, Vote } from "@/types/assistant"

/** The conversation in the panel: questions, answers with what their tools found, the tools
 * at work while one is written, and a failed answer's error with Try again. With no messages
 * yet, a welcome for the user's stage: what the assistant helps with there, and questions to
 * tap, first "What can I do on this page?" on a page with a guide (`onPage`). Under each written
 * answer, thumbs up and down. */
export function AssistantMessages({
  messages,
  streaming,
  signedIn,
  stage,
  onPage,
  onAsk,
  onRetry,
  onVote,
  onNavigate,
  actions,
}: {
  messages: ChatMessage[]
  streaming: boolean
  signedIn: boolean
  // The user's stage ("signed_out" when signed out), which the welcome is about; null while
  // it's unknown.
  stage: string | null
  onPage: boolean
  onAsk: (question: string) => void
  onRetry: () => void
  onVote: (index: number, value: Vote | null) => void
  onNavigate: () => void
  actions: CardActions
}) {
  const t = useTranslations("assistant")
  const common = useTranslations("common")

  if (messages.length === 0) {
    const questions = (stage && WELCOME_QUESTIONS[stage]) || []
    const asks = [
      ...(onPage ? [t("pageQuestion")] : []),
      ...questions.map((key) => t(`welcome.${stage}.questions.${key}`)),
    ]

    return (
      <div className="space-y-6 py-6" data-testid={`welcome-${stage}`}>
        <div className="space-y-2">
          <h2 className="font-heading text-2xl font-medium tracking-tight">
            {signedIn ? t("emptyTitle") : t("emptyTitleFaq")}
          </h2>
          <p className="text-base text-muted-foreground">
            {questions.length > 0 ? t(`welcome.${stage}.text`) : t("emptyText")}
          </p>
        </div>
        <ul className="space-y-2">
          {asks.map((question) => (
            <li key={question}>
              <Button
                variant="outline"
                className="h-auto w-full justify-start rounded-2xl px-4 py-3 text-start text-sm whitespace-normal normal-case"
                onClick={() => onAsk(question)}
              >
                {question}
              </Button>
            </li>
          ))}
        </ul>
      </div>
    )
  }

  const last = messages.at(-1)
  // Screen readers hear each answer once, whole, not every streamed piece of it.
  const answered = !streaming && last?.role === "assistant" ? last.content : ""

  return (
    <>
      <ul className="space-y-3">
        {messages.map((message, index) => {
          if (message.removed) {
            return (
              <li
                key={index}
                className="ms-auto w-fit text-sm text-muted-foreground italic"
                data-testid="message-removed"
              >
                {t("removed")}
              </li>
            )
          }

          if (message.role === "user") {
            return (
              <ChatBubble key={index} role="user" content={message.content} />
            )
          }

          const writing = streaming && index === messages.length - 1
          const last = index === messages.length - 1

          // One card per answer: the tools at work and the dots while it's written, its text,
          // and its error; what its tools found sits right under it.
          return [
            (writing || message.content || message.error) && (
              <ChatBubble
                key={`${index}-text`}
                role="assistant"
                className="space-y-2 border bg-transparent p-4 whitespace-normal"
                // A written answer, saved by the assistant or signed by the help chat, can be
                // voted on, right under it.
                after={
                  !writing &&
                  message.content &&
                  !message.error &&
                  (message.id || message.helpAnswer) && (
                    <AnswerVote
                      value={message.vote ?? null}
                      onVote={(value) => onVote(index, value)}
                    />
                  )
                }
                content={
                  <>
                    {writing &&
                      message.progress?.map((label) => (
                        <p
                          key={label}
                          className="text-xs text-muted-foreground"
                        >
                          {label}
                        </p>
                      ))}
                    {message.content ? (
                      <AnswerMarkdown
                        text={message.content}
                        onNavigate={onNavigate}
                      />
                    ) : (
                      writing && (
                        <span className="flex h-5 items-center gap-1">
                          <ThinkingDots label={common("thinking")} />
                        </span>
                      )
                    )}
                    {message.error && (
                      <span className="flex flex-wrap items-center gap-3 text-destructive">
                        {message.error}
                        {last && (
                          <Button variant="outline" size="sm" onClick={onRetry}>
                            {common("retry")}
                          </Button>
                        )}
                      </span>
                    )}
                  </>
                }
              />
            ),
            message.blocks.length > 0 && (
              <li key={`${index}-blocks`}>
                <AnswerBlocks
                  blocks={message.blocks}
                  actions={actions}
                  onNavigate={onNavigate}
                />
              </li>
            ),
          ]
        })}
      </ul>
      <p aria-live="polite" className="sr-only">
        {answered}
      </p>
    </>
  )
}
