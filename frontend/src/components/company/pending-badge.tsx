"use client"

import { ClockIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import type { ReactElement } from "react"

import { IconStat } from "@/components/common/icon-stat"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"

/** Beside the name of a company waiting for a superadmin's review, for its members only; built
 * like VerifiedBadge. `className` sizes it to the name beside it; `render` makes it a button
 * (the verify dialog's trigger, for owners and admins). */
export function PendingBadge({
  className = "size-6",
  render,
}: {
  className?: string
  render?: ReactElement
}) {
  const t = useTranslations("verify")
  const label = t("pendingBadge")

  if (!render) {
    return (
      <IconStat
        label={label}
        icon={<ClockIcon aria-hidden className={className} />}
      />
    )
  }

  return (
    <Tooltip>
      <TooltipTrigger render={render}>
        <ClockIcon className={className} />
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  )
}
