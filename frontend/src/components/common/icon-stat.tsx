"use client"

import { cn } from "cn"
import type { ComponentProps, ReactNode } from "react"

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { ROUND_ICON_BUTTON } from "@/config/buttons"

/** An icon with what it counts (`children`: a number, a time) or alone (a status, read as an
 * image), its meaning in a tooltip and as its accessible name (`label`). It isn't a control, but
 * hovered it reacts like an icon button: a round background and the icon brightening. The
 * negative margins keep the background from moving what's around it; above a row's link
 * overlay, so hovering it shows the tooltip. `className` colors it (a warning, a verified check). */
export function IconStat({
  label,
  icon,
  children,
  className,
  ...props
}: Omit<ComponentProps<"span">, "children"> & {
  label: string
  icon: ReactNode
  children?: ReactNode
}) {
  const alone = children == null

  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <span
            role={alone ? "img" : undefined}
            aria-label={label}
            className={cn(
              ROUND_ICON_BUTTON,
              "relative z-10 inline-flex shrink-0 items-center align-middle tabular-nums transition-colors",
              alone ? "-m-1 p-1" : "-mx-2 -my-1 gap-1.5 px-2 py-1",
              className
            )}
            {...props}
          />
        }
      >
        {icon}
        {children}
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  )
}
