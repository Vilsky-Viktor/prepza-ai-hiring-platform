"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { TimeFact } from "@/components/common/invite-intro"
import { DemoLogo } from "@/features/landing/components/demo-logo"
import {
  DEMO_COMPANY,
  DEMO_QUESTION_SECONDS,
  DEMO_TITLE,
  DEMO_TOTAL_MINUTES,
} from "@/config/candidates-demo"
import { bdi } from "@/lib/bidi"

// The real page's rules, shortened; phones show the first few.
const RULES = [
  "pick",
  "change",
  "time",
  "unanswered",
  "saved",
  "extraTime",
  "people",
  "stay",
] as const
const PHONE_RULES = 4

/** A candidate's start page, small, for the landing: the company's logo and who invited them,
 * the interview's title and times, its start (`action`), and the rules on a gray area beside them
 * (across the frame on phones, before the start). */
export function DemoInvitation({
  voice,
  action,
}: {
  // Taken by voice: its rule first, as on the real page.
  voice: boolean
  // The start: the pledge, the start button and, by voice, the microphone's step first.
  action: React.ReactNode
}) {
  const t = useTranslations("invite")
  const rules = useTranslations("landing.candidates.rules")

  return (
    <div className="grid flex-1 gap-6 text-center md:grid-cols-[5fr_6fr] md:gap-8">
      <div className="self-center max-md:contents md:space-y-5">
        <div className="space-y-6 md:pb-2.5">
          <div className="flex flex-col items-center gap-3">
            <DemoLogo className="size-20" />
            <p className="text-sm text-muted-foreground">
              {t.rich("invitedYou", {
                company: DEMO_COMPANY,
                ...bdi,
                b: (chunks) => (
                  <span className="font-medium text-foreground">{chunks}</span>
                ),
              })}
            </p>
          </div>
          <p
            data-demo-target="title"
            className="font-heading text-2xl leading-tight font-medium tracking-tight text-balance"
          >
            {DEMO_TITLE}
          </p>
        </div>
        <div className="flex justify-center gap-10">
          <TimeFact
            label={t("timePerQuestion")}
            value={DEMO_QUESTION_SECONDS}
            unit={t("secondsUnit")}
          />
          <TimeFact
            label={t("wholeInterview")}
            value={DEMO_TOTAL_MINUTES}
            unit={t("minutesUnit")}
          />
        </div>
        <div className="max-md:order-last">{action}</div>
      </div>
      {/* The rules, numbered in the brand colour, on a gray area as on the real page: out to the
          frame's edges, the full height of its end side from tablets up; across it on phones. */}
      <ol className="-mx-5 flex flex-col justify-center gap-3 bg-surface px-5 py-6 text-start text-sm text-muted-foreground sm:-mx-8 sm:px-8 md:-my-8 md:ms-0 md:rounded-e-[calc(var(--radius-xl)-1px)] md:py-8">
        {[
          ...(voice ? [t("voice")] : []),
          ...RULES.map((rule) =>
            rules.rich(rule, { company: DEMO_COMPANY, ...bdi })
          ),
        ].map((rule, index) => (
          <li
            key={index}
            className={cn(
              "flex items-baseline gap-3",
              index >= PHONE_RULES && "max-md:hidden",
              // By voice, its rule leaves out the last ones, so both pages are as tall.
              voice && index >= RULES.length - 1 && "md:hidden"
            )}
          >
            <span className="w-5 shrink-0 text-base font-medium text-primary tabular-nums">
              {index + 1}.
            </span>
            <span>{rule}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}
