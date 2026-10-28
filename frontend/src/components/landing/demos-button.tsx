import { cn } from "cn"
import { PlayIcon } from "lucide-react"
import { getTranslations } from "next-intl/server"

import { OUTLINE_BUTTON } from "@/components/landing/section"
import { buttonVariants } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { DEMOS_URL } from "@/constants/landing"

/** "demos": prepza's demo videos on YouTube, in a new tab, as an outline button with a play icon
 * and a tooltip saying where it leads; `label` replaces its text. */
export async function DemosButton({
  label,
  className,
}: {
  label?: string
  className?: string
}) {
  const t = await getTranslations("landing")

  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <a
            href={DEMOS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              buttonVariants({ variant: "outline" }),
              OUTLINE_BUTTON,
              "h-12 px-6 lowercase",
              className
            )}
          />
        }
      >
        <PlayIcon aria-hidden className="size-5" />
        {label ?? t("demos")}
      </TooltipTrigger>
      <TooltipContent>{t("demosTooltip")}</TooltipContent>
    </Tooltip>
  )
}
