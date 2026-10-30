"use client"

import { HashIcon, PlusIcon, SendHorizontalIcon, UsersIcon } from "lucide-react"

import { DemoSlackSidebar } from "@/features/landing/components/demo-slack-sidebar"
import { Wordmark } from "@/components/common/wordmark"
import { useElementSize } from "@/hooks/use-element-size"
import {
  DEMO_REPORT_CANDIDATES,
  DEMO_REPORT_INTERVIEW,
} from "@/config/reports-demo"
import {
  DEMO_SLACK_APP,
  DEMO_SLACK_BUTTON,
  DEMO_SLACK_CHANNEL,
  DEMO_SLACK_FINISHED,
  DEMO_SLACK_UI,
} from "@/config/reports-slack-demo"
import { SLACK } from "@/config/slack"

/** A "finished" message as prepza posts it to Slack (services/notifications/helpers/slack.py,
 * in English like all its Slack messages): who finished the interview, and their grade. */
function finishedText(place: number) {
  const candidate = DEMO_REPORT_CANDIDATES[place]

  return `${candidate.name} (${candidate.email}) finished “${DEMO_REPORT_INTERVIEW.title}”: ${candidate.grade}%.`
}

/** A Slack channel as Slack lays it out, for the landing: the workspace's side menu, then the
 * channel's header with Slack's mark,
 * its name and members; prepza's messages, each from the app (prepza's mark as its square
 * picture, its name, the APP tag and the time) with the blocks prepza sends (a plain-text section
 * and an "Open in prepza" button); and the message box. Scrolled to the newest message once
 * `scrolled`, gliding there. */
export function DemoSlackChannel({ scrolled }: { scrolled: boolean }) {
  const { ref: windowRef, size: windowSize } = useElementSize<HTMLDivElement>()
  const { ref: listRef, size: listSize } = useElementSize<HTMLDivElement>()
  const room =
    windowSize && listSize
      ? Math.max(0, listSize.height - windowSize.height)
      : 0

  return (
    <div className="flex min-h-0 flex-1 overflow-hidden rounded-xl border">
      <DemoSlackSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between gap-3 border-b px-4 py-3">
          <p className="flex items-center gap-2 text-lg font-bold">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={SLACK.logo} alt="" className="size-5" />
            <span className="flex items-center">
              <HashIcon className="size-5" />
              {DEMO_SLACK_CHANNEL}
            </span>
          </p>
          <span className="flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs text-muted-foreground">
            <UsersIcon className="size-3.5" />
            {DEMO_SLACK_UI.members}
          </span>
        </div>
        <div
          ref={windowRef}
          className="relative min-h-0 flex-1 overflow-hidden"
        >
          <div
            ref={listRef}
            style={{ transform: `translateY(${scrolled ? -room : 0}px)` }}
            className="absolute inset-x-0 top-0 space-y-1 py-3 transition-transform duration-3000 ease-in-out motion-reduce:transition-none"
          >
            {DEMO_SLACK_FINISHED.map(({ candidate, time }) => (
              <div key={candidate} className="flex gap-2.5 px-4 py-2">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-surface">
                  <Wordmark short className="text-lg leading-none" />
                </span>
                <div className="min-w-0 space-y-1.5">
                  <p className="flex items-center gap-1.5 text-sm">
                    <span className="font-bold">{DEMO_SLACK_APP}</span>
                    <span className="rounded-sm bg-surface px-1 text-[0.625rem] font-medium text-muted-foreground">
                      {DEMO_SLACK_UI.app}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {time}
                    </span>
                  </p>
                  <p className="text-sm leading-snug break-words">
                    {finishedText(candidate)}
                  </p>
                  <span className="inline-flex h-7 items-center rounded-md border px-3 text-xs font-bold">
                    {DEMO_SLACK_BUTTON}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
        {/* The channel's message box. */}
        <div className="m-3 mt-0 flex items-center gap-2 rounded-lg border px-3 py-2 text-sm text-muted-foreground">
          <PlusIcon className="size-4 shrink-0" />
          <span className="min-w-0 flex-1 truncate">
            {DEMO_SLACK_UI.composer}
          </span>
          <SendHorizontalIcon className="size-4 shrink-0" />
        </div>
      </div>
    </div>
  )
}
