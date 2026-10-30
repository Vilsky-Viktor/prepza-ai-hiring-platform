"use client"

import { HistoryIcon, SparklesIcon, SquarePenIcon, XIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import { Fragment, useEffect, useRef, useState } from "react"

import { ChatBubble, ThinkingDots } from "@/components/common/chat-bubble"
import { AskAgentCards } from "@/features/landing/components/ask-agent-cards"
import {
  DemoActionCard,
  type DemoCardState,
} from "@/features/landing/components/demo-action-card"
import { DemoChatInput } from "@/features/landing/components/demo-chat-input"
import { DemoPointer } from "@/features/landing/components/demo-pointer"
import {
  ASK_AGENT_EMAIL,
  ASK_AGENT_INTERVIEW,
  ASK_AGENT_QUESTIONS,
  ASK_AGENT_RESULTS,
  type AskAgentCard,
  type AskAgentQuestion,
} from "@/config/ask-agent-demo"
import { GLOW_CARD } from "@/config/landing-backgrounds"
import { type DemoStep, pointedAt, useDemoSteps } from "@/hooks/use-demo-steps"
import { bdi, bdiText } from "@/lib/bidi"
import { formatPercent } from "@/lib/format"
import { graphemes, sliceGraphemes } from "@/lib/graphemes"

// A step and what it shows: how many of the chat's items (each question, its answer, and the
// action card before the last answer), the question in the input, the tool at work, the action
// card's state and the card beside the chat that's lit.
type Step = DemoStep & {
  upTo: number
  asking?: AskAgentQuestion
  working?: AskAgentQuestion
  card?: DemoCardState
  lit?: AskAgentCard
}

// One question asked: the pointer clicks into the input, it's typed and sent, and the tool
// reads while the answer is written; `before` items are in the chat already.
function asked(
  question: AskAgentQuestion,
  letters: number,
  before: number,
  lit: AskAgentCard
): Step[] {
  const shared = { upTo: before, lit, asking: question }

  return [
    { name: `aim-${question}`, ms: 800, point: "input", upTo: before, lit },
    { name: `focus-${question}`, ms: 300, click: true, ...shared },
    { name: `type-${question}`, ms: 45, repeat: letters, ...shared },
    { name: `aimSend-${question}`, ms: 600, point: "send", ...shared },
    { name: `send-${question}`, ms: 400, click: true, ...shared },
    {
      name: `work-${question}`,
      ms: 1500,
      point: "none",
      upTo: before + 1,
      lit,
      working: question,
    },
  ]
}

/** The whole conversation: the three questions, typed in `letters` each, with their answers,
 * the last after its action's card is confirmed; then a pause on the complete frame. */
function demoSteps(letters: Record<AskAgentQuestion, number>): Step[] {
  return [
    { name: "start", ms: 1000, point: "none", upTo: 0 },
    ...asked("stats", letters.stats, 0, "info"),
    { name: "answer-stats", ms: 3200, upTo: 2, lit: "info" },
    ...asked("help", letters.help, 2, "help"),
    { name: "answer-help", ms: 4200, upTo: 4, lit: "help" },
    ...asked("invite", letters.invite, 4, "actions"),
    { name: "card", ms: 1600, upTo: 6, card: "pending", lit: "actions" },
    {
      name: "aimConfirm",
      ms: 800,
      point: "confirm",
      upTo: 6,
      card: "pending",
      lit: "actions",
    },
    {
      name: "confirm",
      ms: 400,
      click: true,
      upTo: 6,
      card: "pending",
      lit: "actions",
    },
    {
      name: "running",
      ms: 900,
      point: "none",
      upTo: 6,
      card: "running",
      lit: "actions",
    },
    { name: "done", ms: 3500, upTo: 7, lit: "actions" },
    { name: "end", ms: 1500, upTo: 7 },
  ]
}

/** The assistant's panel answering three questions in turn, played while on screen: how many
 * candidates passed an interview (from its report), how to give extra time (from a guide), and
 * a candidate invited once the pointer confirms the action's card. Beside it, the three things
 * it does, each lit while the chat shows it. A fixed height that scrolls as messages come; with
 * reduced motion, the whole conversation, still. On phones, the three cards alone. */
export function AskAgentDemo() {
  const t = useTranslations("landing.justAsk")
  const locale = useLocale()
  const assistant = useTranslations("assistant")
  const common = useTranslations("common")
  const values = { interview: ASK_AGENT_INTERVIEW, email: ASK_AGENT_EMAIL }
  const questions = Object.fromEntries(
    ASK_AGENT_QUESTIONS.map((key) => [
      key,
      t.markup(`questions.${key}`, { ...values, ...bdiText }),
    ])
  ) as Record<AskAgentQuestion, string>
  const { stats, help, invite } = questions
  // Made once, so the demo plays on as it renders.
  const [steps] = useState(() =>
    demoSteps({
      stats: graphemes(stats).length,
      help: graphemes(help).length,
      invite: graphemes(invite).length,
    })
  )
  const { ref, index, n } = useDemoSteps<HTMLDivElement>(steps)
  const step = steps[index]
  const scroller = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLDivElement>(null)
  const sendRef = useRef<HTMLSpanElement>(null)
  const confirmRef = useRef<HTMLSpanElement>(null)
  const targets = { input: inputRef, send: sendRef, confirm: confirmRef }
  const point = pointedAt(steps, index)
  const asking = step.asking ? questions[step.asking] : null
  const typed = step.name.startsWith("type-")
    ? sliceGraphemes(asking!, n)
    : step.name.startsWith("focus-")
      ? ""
      : asking
  const { passed, total, passMark, best } = ASK_AGENT_RESULTS
  const answer = (text: React.ReactNode) => (
    <ChatBubble
      role="assistant"
      className="border bg-transparent p-4 whitespace-normal"
      content={text}
    />
  )
  const items = [
    <ChatBubble key="q-stats" role="user" content={stats} />,
    answer(
      t("answers.stats", {
        passed,
        total,
        percent: formatPercent((passed / total) * 100, locale),
        passMark: formatPercent(passMark, locale),
        best: formatPercent(best, locale),
      })
    ),
    <ChatBubble key="q-help" role="user" content={help} />,
    answer(
      t.rich("answers.help", {
        link: (chunks) => (
          <span className="underline underline-offset-4">{chunks}</span>
        ),
      })
    ),
    <ChatBubble key="q-invite" role="user" content={invite} />,
    <DemoActionCard
      key="card"
      state={step.card ?? "done"}
      confirmRef={confirmRef}
      pressed={step.name === "confirm"}
    />,
    answer(t.rich("answers.invite", { ...values, ...bdi })),
  ]

  // The latest message comes into view as it's added; back to the top as the chat starts again.
  useEffect(() => {
    const chat = scroller.current

    chat?.scrollTo({
      top: step.upTo === 0 ? 0 : chat.scrollHeight,
      behavior: step.upTo === 0 ? "instant" : "smooth",
    })
  }, [step.upTo, step.working, step.card])

  return (
    <div className="mx-auto grid w-full max-w-4xl gap-4 md:grid-cols-[minmax(0,1fr)_16rem] lg:grid-cols-[minmax(0,1fr)_19rem]">
      <div
        ref={ref}
        aria-hidden
        data-testid="agent-chat"
        className={`relative flex h-120 flex-col overflow-hidden rounded-xl ${GLOW_CARD} text-popover-foreground ring-1 ring-foreground/10 motion-reduce:h-auto max-sm:hidden`}
      >
        <DemoPointer
          target={
            point && point in targets
              ? targets[point as keyof typeof targets]
              : null
          }
          clicking={step.click === true}
          click={index}
        />
        {/* The real panel's own colours, as in the app. */}
        <div className="flex min-h-0 flex-1 flex-col">
          <div className="flex h-14 shrink-0 items-center gap-3 border-b px-4 text-muted-foreground">
            <SparklesIcon className="size-4 shrink-0 text-primary" />
            <p className="flex-1 truncate font-heading text-lg font-medium text-foreground">
              {assistant("title")}
            </p>
            <SquarePenIcon className="size-5" />
            <HistoryIcon className="size-5" />
            <XIcon className="size-5" />
          </div>
          <div
            ref={scroller}
            className="flex-1 overflow-hidden px-4 pt-4 pb-6 text-start"
          >
            <ul className="space-y-3 *:animate-in *:fade-in">
              {/* Mira's welcome, there from the start. */}
              {answer(t("welcome"))}
              {items.slice(0, step.upTo).map((item, at) => (
                <Fragment key={at}>{item}</Fragment>
              ))}
              {step.working && (
                <ChatBubble
                  role="assistant"
                  className="space-y-2 border bg-transparent p-4 whitespace-normal"
                  content={
                    <>
                      <p className="text-xs text-muted-foreground">
                        {t(`steps.${step.working}`)}
                      </p>
                      <span className="flex h-5 items-center gap-1">
                        <ThinkingDots label={common("thinking")} />
                      </span>
                    </>
                  }
                />
              )}
            </ul>
          </div>
          <div className="shrink-0 px-4 pb-4">
            <DemoChatInput
              ref={inputRef}
              sendRef={sendRef}
              text={typed}
              typing={
                step.asking !== undefined && !step.name.startsWith("send-")
              }
              placeholder={assistant("placeholder")}
              pressed={step.name.startsWith("send-")}
            />
          </div>
        </div>
      </div>
      <AskAgentCards lit={step.lit} />
    </div>
  )
}
