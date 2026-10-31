"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { DEMO_PRESSED } from "@/features/landing/components/demo-panel"
import { Caret } from "@/features/landing/components/caret"
import { AiPulse } from "@/components/common/ai-pulse"
import { DemoTopicList } from "@/features/landing/components/demo-topic-list"
import { buttonVariants } from "@/components/ui/button"
import {
  DEMO_ADDED_SUBTOPIC,
  DEMO_CHANGE,
  DEMO_TOPICS,
} from "@/config/create-demo"
import { ADDED, APPLIED, STEPS } from "@/config/create-demo-steps"
import { countedAt } from "@/hooks/use-demo-steps"

// The steps a topic's editor is open for, and those the request for changes is in use.
const EDITING = [
  "open",
  "aimSubtopic",
  "focusSubtopic",
  "adding",
  "aimAdd",
  "add",
  "aimDone",
  "done",
]
const ASKING = ["asking", "aimApply", "apply", "applying"]

/** The create demo's second panel at step `at`, as the topic review: testee's loading mark until the first
 * topic shows; a topic's editor opened and a subtopic added; a change asked of the AI and
 * applied, adding a topic; then the topics approved. Every row keeps its place before it shows,
 * so the panel never changes size. */
export function CreateTopics({ at }: { at: { index: number; n: number } }) {
  const t = useTranslations("generation")
  const step = STEPS[at.index].name
  const shown = countedAt(STEPS, at, "topics", DEMO_TOPICS.length)
  const typed = countedAt(STEPS, at, "adding", DEMO_ADDED_SUBTOPIC.length)
  const added = at.index >= ADDED
  const asking = ASKING.includes(step)
  const asked = countedAt(STEPS, at, "asking", DEMO_CHANGE.length)

  return (
    <div className="flex min-w-0 flex-1 flex-col gap-3 p-2">
      {/* Until the first topic shows, testee's loading mark in the middle of the list's place. The whole
          list keeps its place unseen, so the panel never grows as rows show. */}
      <div className="relative grid flex-1 grid-cols-[minmax(0,1fr)] items-start *:[grid-area:1/1]">
        {shown === 0 && (
          <span className="absolute inset-0 flex items-center justify-center">
            <AiPulse className="size-14" />
          </span>
        )}
        <div className="invisible">
          <DemoTopicList
            shown={DEMO_TOPICS.length}
            added
            applied
            editing={false}
            typed=""
            typing={false}
            pressed={null}
          />
        </div>
        {shown > 0 && (
          <DemoTopicList
            aimed
            shown={shown}
            added={added}
            applied={at.index >= APPLIED}
            editing={EDITING.includes(step)}
            typed={added ? "" : DEMO_ADDED_SUBTOPIC.slice(0, typed)}
            typing={step === "focusSubtopic" || step === "adding"}
            pressed={["open", "add", "done"].includes(step) ? step : null}
          />
        )}
      </div>
      {/* The request for changes, as the review's box (its padding, a few lines tall), and its
          button at the real one's size. */}
      <span
        data-demo-target="ask"
        className="flex min-h-16 items-start rounded-xl bg-surface p-4"
      >
        {asking ? (
          <span className="flex h-5 min-w-0 items-center">
            <span className="truncate">{DEMO_CHANGE.slice(0, asked)}</span>
            {step === "asking" && <Caret />}
          </span>
        ) : (
          <span className="truncate text-muted-foreground">
            {t("changesPlaceholder")}
          </span>
        )}
      </span>
      <div className="flex justify-end">
        <span
          data-demo-target="apply"
          className={buttonVariants({
            className: cn(
              "h-11 px-6 text-base",
              step === "applying" && "opacity-50",
              (step === "apply" || step === "go") && DEMO_PRESSED
            ),
          })}
        >
          {/* As the real button: applying the changes while there are some, else approving
              the topics. */}
          {asking ? t("apply") : t("approve")}
        </span>
      </div>
    </div>
  )
}
