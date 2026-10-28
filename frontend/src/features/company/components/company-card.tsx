"use client"

import { cn } from "cn"
import { MessagesSquareIcon, UserRoundIcon } from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"

import { CompanyLogo } from "@/components/common/company-logo"
import { PendingBadge } from "@/features/company/components/pending-badge"
import { RemoveCompany } from "@/features/company/components/remove-company"
import { VerifiedBadge } from "@/components/common/verified-badge"
import { IconStat } from "@/components/common/icon-stat"
import { CARD_PADDING } from "@/config/cards"
import { firstGrapheme } from "@/lib/graphemes"
import { hasMessage } from "@/lib/messages"
import type { Company } from "@/types/company"

// Hovered or focused, the border turns primary and the logo zooms a little inside its area,
// which fills what the square card leaves above the name whatever the image (laid over it, an
// image never stretches the area).
const CARD =
  "group relative flex aspect-square flex-col overflow-hidden border-y bg-background transition-colors hover:border-primary-gradient has-[a:focus-visible]:border-primary-gradient before:z-10 [--gradient-inset:0px] has-[a:focus-visible]:ring-3 has-[a:focus-visible]:ring-ring/50 sm:rounded-xl sm:border"

const ZOOM =
  "absolute inset-0 flex items-center justify-center transition-transform duration-300 ease-out motion-safe:group-hover:scale-105 motion-safe:group-has-[a:focus-visible]:scale-105"

// The small pills at the top of the card, readable over any logo; rounded-lg nests them in the
// card's rounded corner.
const PILL =
  "flex h-9 items-center gap-2 rounded-lg bg-background/80 px-3 text-sm backdrop-blur"

// Remove shows while the card is hovered or holds focus (focusing it reveals it), and always on
// touch screens, which can't hover.
const REVEAL =
  "transition-opacity [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover:opacity-100 [@media(hover:hover)]:group-focus-within:opacity-100"

/** A company on the companies page: its logo across the top, fading into its name and its count
 * of tests, and over the logo its badges and Remove. The whole card opens the company (`href`). */
export function CompanyCard({
  company,
  href,
  removable,
  onRemoved,
}: {
  company: Company
  href: string
  removable: boolean
  onRemoved: () => void
}) {
  const t = useTranslations("company")
  const roles = useTranslations("roles")
  const count = t("interviewCount", { count: company.interview_count })

  return (
    <div className={CARD}>
      {/* The logo, or the first letter, from border to border; decorative, the name says it.
          Every card has the same structure, so the names line up across a row. */}
      <div
        aria-hidden
        data-testid="company-logo"
        className="relative min-h-0 flex-1 overflow-hidden bg-surface"
      >
        <div className={ZOOM}>
          {company.logo_url ? (
            <CompanyLogo
              url={company.logo_url}
              name=""
              className="size-full object-cover object-center"
            />
          ) : (
            // Without a logo, the first letter on a faint wash of the primary gradient.
            <>
              <span className="absolute inset-0 bg-primary-gradient opacity-10" />
              <span className="relative font-heading text-7xl font-medium text-primary uppercase">
                {firstGrapheme(company.name)}
              </span>
            </>
          )}
        </div>
        {/* Over half the logo, easing in, so the logo melts into the name. */}
        <span className="absolute inset-x-0 bottom-0 h-1/2 bg-linear-to-b from-transparent via-background/40 via-55% to-background" />
      </div>
      <div
        className={cn(CARD_PADDING, "flex shrink-0 items-center gap-3 pt-1")}
      >
        <Link
          href={href}
          title={company.name}
          className="min-w-0 flex-1 truncate font-heading text-xl font-medium outline-none after:absolute after:inset-0"
        >
          {company.name}
        </Link>
        <IconStat
          label={count}
          icon={<MessagesSquareIcon aria-hidden className="size-5" />}
        >
          {company.interview_count}
        </IconStat>
      </div>
      {/* Above the card's link, so the tooltips show and Remove doesn't open the company. */}
      <div
        className={cn(
          CARD_PADDING,
          "absolute inset-x-0 top-0 z-10 flex items-start justify-between gap-2"
        )}
      >
        <span className={PILL}>
          {company.verified_domain && (
            <VerifiedBadge
              domain={company.verified_domain}
              className="size-5"
            />
          )}
          {company.verification_status === "pending" && (
            <PendingBadge className="size-5" />
          )}
          {company.role === "owner" ? (
            <IconStat
              label={t("owner")}
              icon={<UserRoundIcon aria-hidden className="size-5" />}
              className="text-foreground"
            />
          ) : (
            <span>
              {hasMessage(roles, company.role)
                ? roles(company.role)
                : company.role}
            </span>
          )}
        </span>
        {removable && (
          <span className={cn(PILL, REVEAL, "px-0.5")}>
            <RemoveCompany
              companyId={company.id}
              name={company.name}
              onRemoved={onRemoved}
              className="size-8 rounded-md text-foreground [&_svg]:size-5"
            />
          </span>
        )}
      </div>
    </div>
  )
}
