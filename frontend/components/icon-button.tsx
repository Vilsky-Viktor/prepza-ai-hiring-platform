"use client"

import type { ReactElement, ReactNode } from "react"

import { cn } from "cn"

import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"

/** A button that is only an icon: its `label` names it for screen readers and shows on hover.
 * `render` makes it a link (an `<a>`) instead; `className` can make it smaller. `pressed` makes
 * it a toggle (an editor's bold), shown darker while on. */
export function IconButton({
  label,
  disabled,
  pressed,
  onClick,
  render,
  className,
  children,
}: {
  label: string
  disabled?: boolean
  pressed?: boolean
  onClick?: () => void
  render?: ReactElement
  className?: string
  children: ReactNode
}) {
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "size-12 shrink-0 text-muted-foreground hover:text-foreground",
              pressed && "bg-surface text-foreground",
              className
            )}
            aria-label={label}
            aria-pressed={pressed}
            disabled={disabled}
            onClick={onClick}
            render={render}
            nativeButton={!render}
          />
        }
      >
        {children}
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  )
}
