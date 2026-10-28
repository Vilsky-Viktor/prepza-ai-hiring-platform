"use client"

import { cn } from "cn"

import { Button } from "@/components/ui/button"

/** Back up to the job description box at the top of the home page, ready to type. */
export function StartButton({
  label,
  className,
}: {
  label: string
  className?: string
}) {
  function start() {
    window.scrollTo({ top: 0, behavior: "smooth" })
    document.querySelector("textarea")?.focus({ preventScroll: true })
  }

  return (
    <Button
      data-testid="start-button"
      className={cn("h-14 px-10 text-lg", className)}
      onClick={start}
    >
      {label}
    </Button>
  )
}
