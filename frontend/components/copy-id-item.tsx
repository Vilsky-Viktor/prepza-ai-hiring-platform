"use client"

import { CheckIcon, CopyIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { useCopyId } from "@/hooks/use-copy-id"

/** "copy id" in a menu: an icon beside the account's name, named by a tooltip, a real menu item
 * (the arrow keys reach it) that keeps the menu open while its check mark shows. */
export function CopyIdItem({ id }: { id: string }) {
  const common = useTranslations("common")
  const { copied, copy } = useCopyId(id)
  const label = common(copied ? "idCopied" : "copyId")

  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <DropdownMenuItem
            closeOnClick={false}
            onClick={copy}
            aria-label={label}
            data-testid="copy-id"
            data-copied={copied}
            className="size-8 shrink-0 justify-center rounded-full p-0 text-muted-foreground [&_svg:not([class*='size-'])]:size-4"
          />
        }
      >
        {copied ? (
          <CheckIcon aria-hidden className="text-primary" />
        ) : (
          <CopyIcon aria-hidden />
        )}
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  )
}
