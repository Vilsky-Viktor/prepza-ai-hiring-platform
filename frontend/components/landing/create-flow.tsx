"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"
import { useEffect, useRef } from "react"

import { Caret } from "@/components/landing/caret"
import { DemoInterview } from "@/components/landing/demo-interview"
import { DemoInvitePopup } from "@/components/landing/demo-invite-popup"
import { DemoPanel } from "@/components/landing/demo-panel"
import { DemoPointer } from "@/components/landing/demo-pointer"
import { DemoSentNotice } from "@/components/landing/demo-popup"
import { Waiting } from "@/components/landing/demo-waiting"
import { DemoWriting } from "@/components/landing/demo-writing"
import { FlowArrows } from "@/components/landing/flow-arrows"
import { SubtopicChip, TopicCard } from "@/components/landing/topic-card"
import { TypedDescription } from "@/components/landing/typed-description"
import { buttonVariants } from "@/components/ui/button"
import {
  DEMO_ADDED_SUBTOPIC,
  DEMO_CHANGE,
  DEMO_DESCRIPTION,
  DEMO_EDITED,
  DEMO_INVITE_EMAIL,
  DEMO_NEW_TOPIC,
  DEMO_TOPICS,
} from "@/constants/create-demo"
import {
  ADJUST,
  APPLIED,
  DESCRIBE,
  GO,
  INVITING,
  READY,
  RESULT,
  STEPS,
  WRITING,
  WRITTEN,
} from "@/constants/create-demo-steps"
import { countedAt, pointedAt, useDemoSteps } from "@/hooks/use-demo-steps"
import { bdi } from "@/lib/bidi"

// Tailwind's lg: below it the panels stack, one under another.
const STACKED_BELOW = 1024

/** How an interview is created, as three panels joined by arrows: a job description typed and
 * sent; the topics it gives, adjusted by hand and by asking the AI, then approved; and their
 * questions written, then the interview ready, a candidate invited to it. Every row keeps its
 * place before it shows, so the panels never change size. */
export function CreateFlow({
  labels,
}: {
  labels: {
    describe: string
    adjust: string
    ask: string
    ready: string
    status: string
    invite: string
    waiting: string
  }
}) {
  const start = useTranslations("start")
  const generation = useTranslations("generation")
  const share = useTranslations("share")
  const { ref: playRef, skipTo, ...at } = useDemoSteps<HTMLDivElement>(STEPS)
  const readyRef = useRef<HTMLDivElement>(null)
  const step = STEPS[at.index].name
  const letters = countedAt(STEPS, at, "typing", DEMO_DESCRIPTION.length)
  const shown = countedAt(STEPS, at, "topics", DEMO_TOPICS.length)
  const added = countedAt(STEPS, at, "adding", DEMO_ADDED_SUBTOPIC.length)
  const asked = countedAt(STEPS, at, "asking", DEMO_CHANGE.length)
  const adding = step === "open" || step === "adding"
  const asking = ["asking", "aimApply", "apply", "applying"].includes(step)
  const fieldRef = useRef<HTMLParagraphElement>(null)
  const sendRef = useRef<HTMLSpanElement>(null)
  const topicRef = useRef<HTMLSpanElement>(null)
  const askRef = useRef<HTMLDivElement>(null)
  const applyRef = useRef<HTMLSpanElement>(null)
  const inviteRef = useRef<HTMLSpanElement>(null)
  const emailRef = useRef<HTMLDivElement>(null)
  const sendInviteRef = useRef<HTMLSpanElement>(null)
  const emailed = countedAt(STEPS, at, "typingEmail", DEMO_INVITE_EMAIL.length)
  const targets = {
    field: fieldRef,
    send: sendRef,
    topic: topicRef,
    ask: askRef,
    apply: applyRef,
    invite: inviteRef,
    email: emailRef,
    sendInvite: sendInviteRef,
  }
  const point = pointedAt(STEPS, at.index)
  const clicking = STEPS[at.index].click === true

  // The pointer in `panel`, on what it points at there.
  function pointer(panel: string[]) {
    const on = point && panel.includes(point) ? point : null

    return (
      <DemoPointer
        target={on ? targets[on as keyof typeof targets] : null}
        clicking={clicking && on !== null}
        click={at.index}
      />
    )
  }

  // On phones the panels stack, so reaching the last one skips ahead to its generating, rather
  // than leaving it empty while the first two play off screen.
  useEffect(() => {
    const panel = readyRef.current

    if (
      !panel ||
      window.matchMedia(`(min-width: ${STACKED_BELOW}px)`).matches
    ) {
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          skipTo(GO)
        }
      },
      { threshold: 0.5 }
    )
    observer.observe(panel)

    return () => observer.disconnect()
  }, [skipTo])

  return (
    <div
      ref={playRef}
      className="grid flex-1 lg:grid-cols-[minmax(0,5fr)_auto_minmax(0,5fr)_auto_minmax(0,6fr)]"
    >
      <DemoPanel label={labels.describe}>
        {pointer(DESCRIBE)}
        <TypedDescription
          ref={fieldRef}
          sendRef={sendRef}
          full={DEMO_DESCRIPTION}
          letters={step === "empty" ? null : letters}
          typing={step === "typing"}
          placeholder={start("placeholder")}
          pressed={step === "send"}
        />
      </DemoPanel>
      <FlowArrows />
      <DemoPanel label={labels.adjust}>
        {pointer(ADJUST)}
        <div className="flex flex-1 flex-col gap-3">
          {/* Until the first topic shows, "waiting…" in the middle of the list's place. */}
          <div className="relative flex-1">
            {shown === 0 && <Waiting text={labels.waiting} />}
            <ul className="space-y-2">
              {DEMO_TOPICS.map((topic, position) => {
                const edited = topic.name === DEMO_EDITED

                return (
                  <TopicCard
                    key={topic.name}
                    name={topic.name}
                    hidden={position >= shown}
                    highlighted={edited && adding}
                  >
                    {topic.subtopics.map((subtopic) => (
                      <SubtopicChip key={subtopic}>{subtopic}</SubtopicChip>
                    ))}
                    {/* The added subtopic keeps its place, unseen, until it's typed; sized by
                      the whole word (and caret) all along, so nothing moves as it's typed. */}
                    {edited && (
                      <SubtopicChip
                        ref={topicRef}
                        typing={adding}
                        hidden={!adding && added === 0}
                      >
                        <span className="grid *:[grid-area:1/1]">
                          {/* The caret's width as padding. */}
                          <span className="invisible pe-0.5">
                            {DEMO_ADDED_SUBTOPIC}
                          </span>
                          <span className="flex h-4 items-center">
                            {DEMO_ADDED_SUBTOPIC.slice(0, added)}
                            {adding && <Caret />}
                          </span>
                        </span>
                      </SubtopicChip>
                    )}
                  </TopicCard>
                )
              })}
              <TopicCard name={DEMO_NEW_TOPIC.name} hidden={at.index < APPLIED}>
                {DEMO_NEW_TOPIC.subtopics.map((subtopic) => (
                  <SubtopicChip key={subtopic}>{subtopic}</SubtopicChip>
                ))}
              </TopicCard>
            </ul>
          </div>
          {/* The request for changes, as the review's box, and its button. */}
          <div
            ref={askRef}
            className="flex h-10 items-center rounded-full bg-muted px-4 dark:bg-card"
          >
            {asking ? (
              <span className="flex h-5 min-w-0 items-center">
                <span className="truncate">{DEMO_CHANGE.slice(0, asked)}</span>
                {step === "asking" && <Caret />}
              </span>
            ) : (
              <span className="truncate text-muted-foreground">
                {labels.ask}
              </span>
            )}
          </div>
          <div className="flex justify-end">
            <span
              ref={applyRef}
              className={buttonVariants({
                size: "sm",
                className: cn(
                  "lowercase",
                  step === "applying" && "opacity-50",
                  (step === "apply" || step === "go") && "ring-3 ring-ring/50"
                ),
              })}
            >
              {/* As the real button: applying the changes while there are some, else
                  approving the topics. */}
              {asking ? generation("apply") : generation("approve")}
            </span>
          </div>
        </div>
      </DemoPanel>
      <FlowArrows />
      <DemoPanel ref={readyRef} label={labels.ready}>
        {pointer(RESULT)}
        {/* "waiting…" until the topics are approved, then the questions being written, then the
            interview in their place. */}
        <div className="relative grid flex-1 *:[grid-area:1/1]">
          {at.index < WRITING && <Waiting text={labels.waiting} />}
          <div
            data-testid="demo-writing"
            className={cn(
              "flex min-w-0",
              (at.index < WRITING || at.index >= READY) && "invisible opacity-0"
            )}
          >
            <DemoWriting
              topics={WRITTEN}
              ready={countedAt(STEPS, at, "writing", WRITTEN.length)}
            />
          </div>
          <div
            data-testid="demo-interview"
            className={cn(
              "flex min-w-0",
              at.index < READY && "invisible opacity-0"
            )}
          >
            <DemoInterview
              topics={WRITTEN}
              status={labels.status}
              invite={labels.invite}
              inviteRef={inviteRef}
              pressed={step === "invite"}
            />
          </div>
        </div>
        <DemoInvitePopup
          open={INVITING.includes(step)}
          email={DEMO_INVITE_EMAIL.slice(0, emailed)}
          typing={step === "focusEmail" || step === "typingEmail"}
          pressed={step === "sendInvite"}
          emailRef={emailRef}
          sendRef={sendInviteRef}
        />
        <DemoSentNotice
          shown={step === "invited"}
          text={share.rich("sent", { email: DEMO_INVITE_EMAIL, ...bdi })}
        />
      </DemoPanel>
    </div>
  )
}
