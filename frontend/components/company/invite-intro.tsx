"use client"

import { cn } from "cn"
import Link from "next/link"
import { useTranslations } from "next-intl"
import type { ReactNode } from "react"

import { CompanyLogo } from "@/components/company/company-logo"
import { VerifiedBadge } from "@/components/company/verified-badge"
import { InfoCard } from "@/components/warning-card"
import { bdi } from "@/lib/bidi"

/** What a candidate sees before starting: who invited them, the test, the time per question and
 * the rules, then `action` (the start button). A company member's preview shows the same. */
export function InviteIntro({
  company,
  logoUrl,
  verifiedDomain,
  title,
  questionSeconds,
  totalMinutes,
  finished,
  viaLink = false,
  fillScreen,
  action,
}: {
  company: string
  // The inviting company's logo, above who invited them.
  logoUrl?: string | null
  // Its verified domain: the badge beside its name.
  verifiedDomain?: string | null
  title: string | null
  questionSeconds: number
  // The whole interview at that pace, in minutes; left out while it isn't known.
  totalMinutes?: number | null
  finished: boolean
  // Opened from the test's shareable link: their own link comes by email, and extra time needs
  // a personal invite.
  viaLink?: boolean
  // Fills the screen from md up unless false: false inside a company's own site (the embed),
  // whose frame grows to fit its content, so a height taken from the frame would grow it without
  // end.
  fillScreen?: boolean
  action: ReactNode
}) {
  const t = useTranslations("invite")
  const height = screenHeight(fillScreen !== false)

  const header = (
    <div className="space-y-4">
      {/* The logo, with who invited them under it, centered together. */}
      {company && (
        <div className="flex flex-col items-center justify-center gap-4 pb-3">
          {logoUrl && (
            <CompanyLogo
              url={logoUrl}
              name={company}
              className="h-28 w-auto max-w-56 shrink-0 rounded-3xl object-contain"
            />
          )}
          <p className="text-base text-muted-foreground">
            {t.rich("invitedYou", {
              company,
              ...bdi,
              b: (chunks) => (
                <span className="font-medium text-foreground">
                  {chunks}
                  {verifiedDomain && (
                    <VerifiedBadge
                      domain={verifiedDomain}
                      className="ms-1 size-4"
                    />
                  )}
                </span>
              ),
            })}
          </p>
        </div>
      )}
      {/* Small and quiet, yet readable (4.5:1): prepza hasn't checked who this company is. */}
      {company && !verifiedDomain && (
        <p className="text-xs text-muted-foreground">{t("unverified")}</p>
      )}
      <h1
        className={cn(
          "font-heading text-3xl leading-[1.15] font-medium tracking-tight text-balance sm:text-4xl sm:leading-[1.15]",
          title && "normal-case"
        )}
      >
        {title ?? t("fallbackTitle")}
      </h1>
    </div>
  )

  if (finished) {
    return (
      <div className="w-full space-y-8 text-center">
        {header}
        <InfoCard className="mx-auto w-fit text-start">
          {t("finished")}
        </InfoCard>
      </div>
    )
  }

  // The test and its start on the left, the rules on the right; stacked on phones, the start
  // after the rules.
  return (
    // From md up the grid fills the screen (these pages have no header), so the rules can run its
    // full height.
    <div
      className={cn(
        "grid w-full items-center gap-10 max-md:text-center md:grid-cols-[5fr_6fr] md:gap-16",
        height.grid
      )}
    >
      <div className="space-y-8 text-center max-md:contents">
        {header}
        {/* The time per question and, when known, the whole interview's, side by side. */}
        <div className="flex justify-center gap-12">
          <TimeFact
            label={t("timePerQuestion")}
            value={questionSeconds}
            unit={t("secondsUnit")}
          />
          {totalMinutes ? (
            <TimeFact
              label={t("wholeInterview")}
              value={totalMinutes}
              unit={t("minutesUnit")}
              testId="total-minutes"
            />
          ) : null}
        </div>
        <div className="max-md:order-last">{action}</div>
      </div>
      {/* The rules in a gray card, numbered in the brand color; on phones it spans the screen,
          with square corners. Beside the start (md up) it runs the screen's full height, square,
          scrolling inside when the rules don't fit. */}
      <ol
        data-testid="invite-rules"
        className={cn(
          "-mx-6 space-y-4 bg-muted p-8 text-start text-base text-muted-foreground sm:mx-0 sm:rounded-2xl sm:p-10 md:flex md:flex-col md:self-stretch md:overflow-y-auto md:rounded-none md:[&>li:first-child]:mt-auto md:[&>li:last-child]:mb-auto",
          height.rules
        )}
      >
        {[
          t("pickOne"),
          t("changePick"),
          t("timeRunsOut"),
          t("unanswered"),
          viaLink ? t("savedLink") : t("saved"),
          // Accommodations, and the human decision behind the score.
          t.rich(viaLink ? "extraTimeLink" : "extraTime", {
            company: company || t("theCompany"),
            ...bdi,
          }),
          t.rich("people", { company: company || t("theCompany"), ...bdi }),
          t.rich("stay", {
            link: (chunks) => (
              // In a new tab: the interview stays open, also inside a company's site, whose
              // frame shows nothing else of prepza.
              <Link
                href="/privacy"
                target="_blank"
                rel="noopener"
                className="underline underline-offset-4"
              >
                {chunks}
              </Link>
            ),
          }),
        ].map((rule, index) => (
          <li key={index} className="flex items-baseline gap-4">
            <span className="w-6 shrink-0 text-xl font-medium text-primary tabular-nums">
              {index + 1}.
            </span>
            <span>{rule}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}

/** One time before the start: its label over a large number and its unit. */
export function TimeFact({
  label,
  value,
  unit,
  testId,
}: {
  label: string
  value: number
  unit: string
  testId?: string
}) {
  return (
    <p className="text-base text-muted-foreground" data-testid={testId}>
      <span className="text-sm">{label}</span>
      <span className="block">
        <span className="text-3xl font-medium text-foreground tabular-nums">
          {value}
        </span>{" "}
        {unit}
      </span>
    </p>
  )
}

/** From md up the page fills the screen and the rules scroll within it; embedded, neither. */
function screenHeight(fill: boolean) {
  return fill
    ? { grid: "md:min-h-dvh", rules: "md:max-h-dvh" }
    : { grid: "", rules: "" }
}
