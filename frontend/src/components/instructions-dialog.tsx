"use client"

import { useTranslations } from "next-intl"
import { useRef } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

/** An integration's one Instructions button, beside Connect: a dialog with everything to know,
 * connected or not: `steps`, numbered (when it has a simple list), after any setup still to do (`children`, with the steps
 * then under their own `stepsTitle`). Open by itself after connecting when the caller says so. */
export function InstructionsDialog({
  title,
  steps,
  stepsTitle,
  open,
  onOpenChange,
  children,
}: {
  title: string
  steps?: string[]
  stepsTitle?: string
  open?: boolean
  onOpenChange?: (open: boolean) => void
  children?: React.ReactNode
}) {
  const t = useTranslations("ats")
  const common = useTranslations("common")
  // Opens on the dialog itself, not its first field, so a copy field isn't selected and scrolled.
  const popup = useRef<HTMLDivElement>(null)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger
        data-testid="instructions"
        render={
          <Button variant="outline" className="h-10 shrink-0 px-5 text-base" />
        }
      >
        {t("instructions")}
      </DialogTrigger>
      <DialogContent
        ref={popup}
        initialFocus={popup}
        showCloseButton={false}
        className="max-h-[90dvh] max-sm:h-dvh max-sm:max-h-dvh sm:max-w-2xl"
      >
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        {children}
        {children && stepsTitle && (
          <h3 className="text-lg font-medium">{stepsTitle}</h3>
        )}
        {steps && (
          <ol className="list-decimal space-y-3 ps-5 text-base text-muted-foreground">
            {steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        )}
        <DialogFooter>
          <DialogClose
            render={
              <Button variant="outline" className="h-10 px-5 text-base" />
            }
          >
            {common("close")}
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
