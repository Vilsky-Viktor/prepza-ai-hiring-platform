import { cn } from "cn"
import type { ComponentProps, ReactNode } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { SEARCH_OVER_LIST } from "@/constants/lists"

export function InputAction({
  action,
  disabled,
  icon,
  addon,
  ...props
}: ComponentProps<typeof Input> & {
  action: string
  disabled?: boolean
  icon?: ReactNode
  // Controls inside the field, before its button (a search's filters).
  addon?: ReactNode
}) {
  if (addon) {
    return (
      // On phones the text takes its own row and the controls the row under it, inside the same
      // field, which spans the screen with square corners; from sm up it's one rounded row.
      <div
        className={cn(
          "relative -mx-6 flex min-w-0 flex-1 flex-wrap items-center gap-2 border border-transparent bg-surface ps-3 pe-3 pb-3 transition-colors focus-within:border-ring-gradient sm:mx-0 sm:flex-nowrap sm:rounded-xl sm:ps-0 sm:pb-0",
          SEARCH_OVER_LIST
        )}
      >
        <Input
          className="h-16 min-w-0 flex-1 basis-full border-0 bg-transparent px-3 text-lg focus-visible:ring-0 sm:basis-auto sm:px-6 md:text-lg dark:bg-transparent"
          {...props}
        />
        {addon}
        <Button
          type="submit"
          disabled={disabled}
          size="icon"
          className="ms-auto size-10 shrink-0 rounded-lg sm:ms-0"
          aria-label={action}
        >
          {icon ?? action}
        </Button>
      </div>
    )
  }

  // The site's big borderless field; an icon button, or a text one (e.g. "share & start").
  return (
    <div
      className={cn(
        "relative min-w-0 flex-1 rounded-xl border border-transparent transition-colors focus-within:border-ring-gradient searched:max-sm:-mx-6",
        SEARCH_OVER_LIST
      )}
    >
      <Input
        className={cn(
          "h-16 border-0 px-6 text-lg focus-visible:ring-0 md:text-lg",
          SEARCH_OVER_LIST,
          icon ? "pe-20" : "pe-48"
        )}
        {...props}
      />
      <Button
        type="submit"
        disabled={disabled}
        size={icon ? "icon" : "default"}
        className={
          icon
            ? "absolute end-3 top-3 size-10 rounded-lg"
            : "absolute end-3 top-3 h-10 px-5 text-base"
        }
        aria-label={icon ? action : undefined}
      >
        {icon ?? action}
      </Button>
    </div>
  )
}
