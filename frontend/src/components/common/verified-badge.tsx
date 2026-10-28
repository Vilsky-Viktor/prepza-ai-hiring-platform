"use client"

import { BadgeCheckIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { IconStat } from "@/components/common/icon-stat"
import { bdiText } from "@/lib/bidi"

/** The check beside a verified company's name, wherever it's shown; its tooltip names the
 * domain an admin's work email verified. `className` sizes it to the name beside it. */
export function VerifiedBadge({
  domain,
  className = "size-6",
}: {
  domain: string
  className?: string
}) {
  const t = useTranslations("verify")
  const label = t.markup("verified", { domain, ...bdiText })

  return (
    <IconStat
      label={label}
      icon={<BadgeCheckIcon aria-hidden className={className} />}
      className="text-primary hover:text-primary"
    />
  )
}
