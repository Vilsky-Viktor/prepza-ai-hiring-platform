"use client"

import { useTranslations } from "next-intl"

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"

// The tooltip's text by where it shows: for someone who can't edit the name, and for an owner or
// admin in the candidate list or on the candidate's page, where they can enter it.
const HINTS = {
  view: "noNameHint",
  list: "noNameHintList",
  page: "noNameHintPage",
} as const

/** "No name yet", for a candidate whose name isn't known, with when it gets filled in a
 * tooltip (`hint`). */
export function NoName({ hint = "view" }: { hint?: keyof typeof HINTS }) {
  const t = useTranslations("candidates")

  return (
    <Tooltip>
      <TooltipTrigger render={<span data-testid="no-name" />}>
        {t("noName")}
      </TooltipTrigger>
      <TooltipContent>{t(HINTS[hint])}</TooltipContent>
    </Tooltip>
  )
}
