"use client"

import { MessagesSquareIcon, UserRoundIcon } from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"

import { CompanyLogo } from "@/components/company/company-logo"
import { PendingBadge } from "@/components/company/pending-badge"
import { RemoveCompany } from "@/components/company/remove-company"
import { VerifiedBadge } from "@/components/company/verified-badge"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { firstGrapheme } from "@/lib/graphemes"
import { hasMessage } from "@/lib/messages"
import type { Company } from "@/types/company"

// Hovered or focused, the border turns primary and the logo zooms a little inside its area,
// which keeps its 4:3 whatever the image (laid over it, an image never stretches the area).
const CARD =
  "group relative overflow-hidden border-y bg-background transition-colors hover:border-primary has-[a:focus-visible]:border-primary has-[a:focus-visible]:ring-3 has-[a:focus-visible]:ring-ring/50 sm:rounded-2xl sm:border"

const ZOOM =
  "absolute inset-0 flex items-center justify-center transition-transform duration-300 ease-out motion-safe:group-hover:scale-105 motion-safe:group-has-[a:focus-visible]:scale-105"

// The small pills at the top of the card, readable over any logo.
const PILL =
  "flex h-9 items-center gap-2 rounded-full bg-background/80 px-3 text-sm backdrop-blur"

/** A company on the companies page: its logo across the top, fading into its name, and over the
 * logo its badges, its count of tests and Remove. The whole card opens the company (`href`). */
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
        className="relative aspect-4/3 overflow-hidden bg-muted"
      >
        <div className={ZOOM}>
          {company.logo_url ? (
            <CompanyLogo
              url={company.logo_url}
              name=""
              className="size-full object-cover object-center"
            />
          ) : (
            <span className="font-heading text-7xl font-medium text-muted-foreground uppercase">
              {firstGrapheme(company.name)}
            </span>
          )}
        </div>
        <span className="absolute inset-x-0 bottom-0 h-1/3 bg-linear-to-b from-transparent to-background" />
      </div>
      <div className="px-5 pt-1 pb-5">
        <Link
          href={href}
          title={company.name}
          className="block truncate font-heading text-xl font-medium outline-none after:absolute after:inset-0"
        >
          {company.name}
        </Link>
      </div>
      {/* Above the card's link, so the tooltips show and Remove doesn't open the company. */}
      <div className="absolute inset-x-0 top-0 z-10 flex items-start justify-between gap-2 p-3">
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
            <Tooltip>
              <TooltipTrigger
                render={<span role="img" aria-label={t("owner")} />}
              >
                <UserRoundIcon className="size-5" />
              </TooltipTrigger>
              <TooltipContent>{t("owner")}</TooltipContent>
            </Tooltip>
          ) : (
            <span>
              {hasMessage(roles, company.role)
                ? roles(company.role)
                : company.role}
            </span>
          )}
        </span>
        <span className={`${PILL} ${removable ? "pe-0.5" : ""}`}>
          <Tooltip>
            <TooltipTrigger
              render={
                <span
                  className="flex items-center gap-1.5 tabular-nums"
                  aria-label={count}
                />
              }
            >
              <MessagesSquareIcon aria-hidden className="size-5" />
              {company.interview_count}
            </TooltipTrigger>
            <TooltipContent>{count}</TooltipContent>
          </Tooltip>
          {removable && (
            <RemoveCompany
              companyId={company.id}
              name={company.name}
              onRemoved={onRemoved}
              className="size-8 rounded-full text-foreground [&_svg]:size-5"
            />
          )}
        </span>
      </div>
    </div>
  )
}
