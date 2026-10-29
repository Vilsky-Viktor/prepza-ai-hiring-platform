"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"

/** The shortcut that sends a long text box (⌘/Ctrl + Enter), small and muted in its bottom start
 * corner; hidden on touch screens, which have no such keys. */
export function SubmitHint({ className }: { className?: string }) {
  const common = useTranslations("common")

  return (
    <p
      data-testid="submit-hint"
      className={cn(
        "text-xs text-muted-foreground pointer-coarse:hidden",
        className
      )}
    >
      {common("submitHint")}
    </p>
  )
}
