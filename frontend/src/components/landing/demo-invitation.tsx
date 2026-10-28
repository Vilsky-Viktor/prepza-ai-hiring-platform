"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

import { TimeFact } from "@/components/company/invite-intro"
import { DemoLogo } from "@/components/landing/demo-logo"
import { buttonVariants } from "@/components/ui/button"
import {
  DEMO_COMPANY,
  DEMO_QUESTION_SECONDS,
  DEMO_TITLE,
  DEMO_TOTAL_MINUTES,
} from "@/constants/candidates-demo"
import { START_BUTTON } from "@/constants/start-page"
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
 * the interview's title and times, its start button, and the rules on a gray area beside them
 * (across the frame on phones, before the start). */
export function DemoInvitation({
  titleRef,
  startRef,
  pressed,
}: {
  titleRef: React.Ref<HTMLParagraphElement>
  startRef: React.Ref<HTMLSpanElement>
  pressed: boolean
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
            ref={titleRef}
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
        <div className="max-md:order-last">
          <span
            ref={startRef}
            className={buttonVariants({
              className: cn(START_BUTTON, pressed && "ring-3 ring-ring/50"),
            })}
          >
            {t("start")}
          </span>
        </div>
      </div>
      {/* The rules, numbered in the brand colour, on a gray area as on the real page: out to the
          frame's edges, the full height of its end side from tablets up; across it on phones. */}
      <ol className="-mx-5 flex flex-col justify-center gap-3 bg-surface px-5 py-6 text-start text-sm text-muted-foreground sm:-mx-8 sm:px-8 md:-my-8 md:ms-0 md:rounded-e-[calc(var(--radius-xl)-1px)] md:py-8">
        {RULES.map((rule, index) => (
          <li
            key={rule}
            className={cn(
              "flex items-baseline gap-3",
              index >= PHONE_RULES && "max-md:hidden"
            )}
          >
            <span className="w-5 shrink-0 text-base font-medium text-primary tabular-nums">
              {index + 1}.
            </span>
            <span>{rules.rich(rule, { company: DEMO_COMPANY, ...bdi })}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}
