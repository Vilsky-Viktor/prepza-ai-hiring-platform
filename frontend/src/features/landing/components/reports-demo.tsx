"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"
import { useMemo, useState } from "react"

import { DemoCandidates } from "@/features/landing/components/demo-candidates"
import {
  DemoChat,
  type DemoMessage,
} from "@/features/landing/components/demo-chat"
import { DemoDownloadCue } from "@/features/landing/components/demo-download-cue"
import { DemoNotes } from "@/features/landing/components/demo-notes"
import { DemoPanel } from "@/features/landing/components/demo-panel"
import { DemoPointer } from "@/features/landing/components/demo-pointer"
import { DemoReport } from "@/features/landing/components/demo-report"
import { DemoSentNotice } from "@/features/landing/components/demo-popup"
import { DemoSharePopup } from "@/features/landing/components/demo-share"
import { DemoSlackChannel } from "@/features/landing/components/demo-slack-channel"
import {
  DEMO_BEST,
  DEMO_CHAT_TIMES,
  DEMO_FLAGGED,
  DEMO_REPORT_CANDIDATES,
  DEMO_RUNNER_UP,
  DEMO_SHARE_EMAIL,
} from "@/config/reports-demo"
import {
  REPORT_TARGETS,
  type ReportStep,
  reportSteps,
} from "@/config/reports-demo-steps"
import {
  countedAt,
  pointedAt,
  stepIndex,
  useDemoSteps,
} from "@/hooks/use-demo-steps"
import { bdi } from "@/lib/bidi"

// The list's action pressed at each step that presses one.
const LIST_PRESSES: Record<string, "download" | "share"> = {
  download: "download",
  share: "share",
}

/** What's pressed in the share dialog at step `name`. */
function popupPressed(name: string) {
  if (name === "send") {
    return "send"
  }

  return name.startsWith("whatsApp") ? "whatsApp" : null
}

/** The chat's messages at step `index`: each turn's summary once it arrives, then its line once
 * sent. */
function messagesAt(
  steps: ReportStep[],
  index: number,
  lines: [string, string]
): DemoMessage[] {
  const after = (name: string) => index >= stepIndex(steps, name)
  const messages: DemoMessage[] = []

  ;[DEMO_BEST, DEMO_FLAGGED].forEach((candidate, at) => {
    if (after(`summary${at}`)) {
      messages.push({
        summary: DEMO_REPORT_CANDIDATES[candidate],
        time: DEMO_CHAT_TIMES[at * 2],
      })
    }

    if (after(`sent${at}`)) {
      messages.push({ text: lines[at], time: DEMO_CHAT_TIMES[at * 2 + 1] })
    }
  })

  return messages
}

/** Reports and sharing, played by a pointer in one panel of a fixed size: the interview's
 * candidates, their PDF downloaded and emailed to the manager; the best candidate's page shared
 * to WhatsApp (its text summary, then a line typed); the flagged one's the same; then a note
 * posted on the interview's notes, and last the Slack channel with testee's messages. Each screen fades out and the next in; the share dialog, the
 * download and the notices lie over them. With reduced motion, the Slack channel at its newest message. */
export function ReportsDemo() {
  const t = useTranslations("landing.shareReports")
  const report = useTranslations("report")
  const lines: [string, string] = [t("chat.best"), t("chat.flagged")]
  const note = t("proceeding", {
    first: DEMO_REPORT_CANDIDATES[DEMO_BEST].name,
    second: DEMO_REPORT_CANDIDATES[DEMO_RUNNER_UP].name,
  })
  const steps = useMemo(
    () => reportSteps(DEMO_BEST, DEMO_FLAGGED, lines, DEMO_SHARE_EMAIL, note),
    // The texts decide the steps' lengths.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [lines[0], lines[1], note]
  )
  const { ref, ...at } = useDemoSteps<HTMLDivElement>(steps)
  const step = steps[at.index]
  const after = (name: string) => at.index >= stepIndex(steps, name)
  // What the pointer moves to: found in the screen shown when the pointer looks for it.
  const [targets] = useState(() =>
    Object.fromEntries(
      REPORT_TARGETS.map((name) => [
        name,
        {
          get current() {
            return (
              ref.current?.querySelector<HTMLElement>(
                `[data-shown=true] [data-demo-target=${name}], [data-overlay] [data-demo-target=${name}]`
              ) ?? null
            )
          },
        },
      ])
    )
  )
  const point = pointedAt(steps, at.index)
  const turn = after("aimRow1") ? 1 : 0
  const typedTurn = countedAt(steps, at, `typing${turn}`, lines[turn].length)
  const chatTyped = after(`sent${turn}`) ? "" : lines[turn].slice(0, typedTurn)

  // A screen, shown while it's the step's, fading in after the one before has faded out.
  function screen(shown: boolean, key: string, content: React.ReactNode) {
    return (
      <div
        key={key}
        data-shown={shown}
        className={cn(
          "flex min-h-0 flex-col transition-[opacity,translate,visibility]",
          shown
            ? "delay-200 duration-500"
            : "invisible translate-y-2 opacity-0 duration-200"
        )}
      >
        {content}
      </div>
    )
  }

  return (
    <div
      data-testid="reports-demo"
      data-step={step.name}
      className="mx-auto w-full max-w-5xl"
    >
      <DemoPanel ref={ref}>
        <DemoPointer
          target={targets[point ?? ""] ?? null}
          clicking={step.click === true}
          click={at.index}
        />
        {/* As tall on every screen, so nothing moves as they change. */}
        <div className="grid h-176 grid-cols-[minmax(0,1fr)] grid-rows-[minmax(0,1fr)] p-2 *:min-w-0 *:[grid-area:1/1] max-sm:h-160 sm:h-152 sm:p-5">
          {screen(
            step.screen === "list",
            "list",
            <DemoCandidates
              pressed={LIST_PRESSES[step.name] ?? null}
              opened={
                step.name.startsWith("openRow")
                  ? (step.candidate ?? steps[at.index + 1]?.candidate ?? null)
                  : null
              }
            />
          )}
          {[DEMO_BEST, DEMO_FLAGGED].map((candidate) =>
            screen(
              step.screen === "page" && step.candidate === candidate,
              `page${candidate}`,
              <DemoReport
                candidate={DEMO_REPORT_CANDIDATES[candidate]}
                scrolled={step.scrolled ?? 0}
                pressed={step.name.startsWith("share")}
              />
            )
          )}
          {screen(
            step.screen === "chat",
            "chat",
            <DemoChat
              messages={messagesAt(steps, at.index, lines)}
              typed={chatTyped}
              typing={step.name === `typing${turn}`}
              pressed={step.name === `send${turn}`}
            />
          )}
          {screen(
            step.screen === "slack",
            "slack",
            <DemoSlackChannel scrolled={after("slackScrolled")} />
          )}
          {screen(
            step.screen === "notes",
            "notes",
            <DemoNotes
              typed={
                after("post")
                  ? ""
                  : note.slice(
                      0,
                      countedAt(steps, at, "typingNote", note.length)
                    )
              }
              pressed={step.name === "post"}
              posted={after("posted") ? note : null}
            />
          )}
        </div>
        <div data-overlay>
          <DemoSharePopup
            open={step.popup === true}
            email={
              step.screen === "list"
                ? DEMO_SHARE_EMAIL.slice(
                    0,
                    countedAt(steps, at, "typingEmail", DEMO_SHARE_EMAIL.length)
                  )
                : ""
            }
            typing={["focusEmail", "typingEmail"].includes(step.name)}
            pressed={popupPressed(step.name)}
          />
        </div>
        <DemoDownloadCue shown={step.download === true} />
        <DemoSentNotice
          shown={step.notice === true}
          text={report.rich("sent", { email: DEMO_SHARE_EMAIL, ...bdi })}
        />
      </DemoPanel>
    </div>
  )
}
