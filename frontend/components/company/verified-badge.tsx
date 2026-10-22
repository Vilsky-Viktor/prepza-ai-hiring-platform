"use client"

import { BadgeCheckIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
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
    <Tooltip>
      <TooltipTrigger
        render={
          <span
            role="img"
            aria-label={label}
            className="relative z-10 inline-flex shrink-0 align-middle text-primary"
          />
        }
      >
        <BadgeCheckIcon className={className} />
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  )
}
