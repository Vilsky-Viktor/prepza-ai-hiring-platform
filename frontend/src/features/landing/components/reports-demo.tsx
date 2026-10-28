"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"
import { useRef } from "react"

import { DemoCandidates } from "@/features/landing/components/demo-candidates"
import { DemoChat } from "@/features/landing/components/demo-chat"
import { DemoPanel } from "@/features/landing/components/demo-panel"
import { DemoPointer } from "@/features/landing/components/demo-pointer"
import { DemoReport } from "@/features/landing/components/demo-report"
import { DemoSentNotice } from "@/features/landing/components/demo-popup"
import { DemoSharePopup } from "@/features/landing/components/demo-share"
import { DEMO_SHARE_EMAIL } from "@/config/reports-demo"
import {
  countedAt,
  type DemoStep,
  pointedAt,
  useDemoSteps,
} from "@/hooks/use-demo-steps"
import { bdi } from "@/lib/bidi"

// A step and what it shows: the screen, whether the share popup is open or the "sent" notice
// shows, and how far down the report is scrolled (0 to 1).
type Screen = "list" | "report" | "chat"
type Step = DemoStep & {
  screen: Screen
  popup?: boolean
  notice?: boolean
  scrolled?: number
}

// On the candidates list the pointer shares the report by email: the popup, the address
// typed, sent. It opens a candidate's report, which scrolls through their answers, and shares
// it to WhatsApp, which gets the text summary. Last, the report at its top: the still frame.
const STEPS: Step[] = [
  { name: "list", ms: 1600, point: "none", screen: "list" },
  { name: "aimListShare", ms: 900, point: "listShare", screen: "list" },
  { name: "listShare", ms: 450, click: true, screen: "list", popup: true },
  { name: "aimEmail", ms: 700, point: "email", screen: "list", popup: true },
  { name: "focusEmail", ms: 300, click: true, screen: "list", popup: true },
  {
    name: "typing",
    ms: 70,
    repeat: DEMO_SHARE_EMAIL.length,
    screen: "list",
    popup: true,
  },
  { name: "aimSend", ms: 700, point: "send", screen: "list", popup: true },
  { name: "send", ms: 450, click: true, screen: "list", popup: true },
  { name: "sent", ms: 2200, point: "none", screen: "list", notice: true },
  { name: "aimRow", ms: 900, point: "row", screen: "list", notice: true },
  { name: "openRow", ms: 450, click: true, screen: "list", notice: true },
  { name: "report", ms: 1400, point: "none", screen: "report" },
  { name: "scrollMid", ms: 2600, screen: "report", scrolled: 0.5 },
  { name: "scrollEnd", ms: 2600, screen: "report", scrolled: 1 },
  {
    name: "aimReportShare",
    ms: 900,
    point: "reportShare",
    screen: "report",
    scrolled: 1,
  },
  {
    name: "reportShare",
    ms: 450,
    click: true,
    screen: "report",
    scrolled: 1,
    popup: true,
  },
  {
    name: "aimWhatsApp",
    ms: 900,
    point: "whatsApp",
    screen: "report",
    scrolled: 1,
    popup: true,
  },
  {
    name: "whatsApp",
    ms: 450,
    click: true,
    screen: "report",
    scrolled: 1,
    popup: true,
  },
  { name: "chat", ms: 6000, point: "none", screen: "chat" },
  { name: "end", ms: 1500, screen: "report" },
]
const REPORT = STEPS.findIndex(({ name }) => name === "report")

/** Reports and sharing, played by a pointer in one panel of a fixed height: an interview's
 * candidates and their report emailed, then one candidate's report scrolled through and shared
 * to WhatsApp as a text summary. One screen fades out and the next in; the popup and the notice
 * lie over them. With reduced motion, the candidate's report at its top. */
export function ReportsDemo() {
  const report = useTranslations("report")
  const { ref, ...at } = useDemoSteps<HTMLDivElement>(STEPS)
  const step = STEPS[at.index]
  const listShareRef = useRef<HTMLSpanElement>(null)
  const rowRef = useRef<HTMLLIElement>(null)
  const reportShareRef = useRef<HTMLSpanElement>(null)
  const emailRef = useRef<HTMLDivElement>(null)
  const sendRef = useRef<HTMLSpanElement>(null)
  const whatsAppRef = useRef<HTMLSpanElement>(null)
  const targets = {
    listShare: listShareRef,
    row: rowRef,
    reportShare: reportShareRef,
    email: emailRef,
    send: sendRef,
    whatsApp: whatsAppRef,
  }
  const point = pointedAt(STEPS, at.index)
  // The address is typed into the list's popup only; the report's opens empty.
  const letters =
    at.index < REPORT
      ? countedAt(STEPS, at, "typing", DEMO_SHARE_EMAIL.length)
      : 0

  // A screen, shown while it's the step's, fading in after the one before has faded out.
  function screen(name: Screen, content: React.ReactNode) {
    return (
      <div
        className={cn(
          "flex min-h-0 flex-col transition-[opacity,translate,visibility]",
          step.screen === name
            ? "delay-200 duration-500"
            : "invisible translate-y-2 opacity-0 duration-200"
        )}
      >
        {content}
      </div>
    )
  }

  return (
    <div className="mx-auto w-full max-w-5xl">
      <DemoPanel ref={ref}>
        <DemoPointer
          target={
            point && point in targets
              ? targets[point as keyof typeof targets]
              : null
          }
          clicking={step.click === true}
          click={at.index}
        />
        {/* As tall on every screen, so nothing moves as they change. */}
        <div className="grid h-136 grid-cols-[minmax(0,1fr)] grid-rows-[minmax(0,1fr)] p-2 *:min-w-0 *:[grid-area:1/1] sm:h-128 sm:p-5">
          {screen(
            "list",
            <DemoCandidates
              shareRef={listShareRef}
              sharePressed={step.name === "listShare"}
              rowRef={rowRef}
              rowPressed={step.name === "openRow"}
            />
          )}
          {screen(
            "report",
            <DemoReport
              scrolled={step.scrolled ?? 0}
              gliding={step.name.startsWith("scroll")}
              shareRef={reportShareRef}
              sharePressed={step.name === "reportShare"}
            />
          )}
          {screen("chat", <DemoChat shown={step.screen === "chat"} />)}
        </div>
        <DemoSharePopup
          open={step.popup === true}
          email={DEMO_SHARE_EMAIL.slice(0, letters)}
          typing={["focusEmail", "typing"].includes(step.name)}
          pressed={
            step.name === "send"
              ? "send"
              : step.name === "whatsApp"
                ? "whatsApp"
                : null
          }
          emailRef={emailRef}
          sendRef={sendRef}
          whatsAppRef={whatsAppRef}
        />
        <DemoSentNotice
          shown={step.notice === true}
          text={report.rich("sent", { email: DEMO_SHARE_EMAIL, ...bdi })}
        />
      </DemoPanel>
    </div>
  )
}
