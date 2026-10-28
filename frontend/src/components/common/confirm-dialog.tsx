"use client"

import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

/** Asks before something that can't be undone: a title, what happens, "keep" and the red
 * `confirm` button. Closing is off while `busy`. `children` go under the text (a box to tick
 * first), and `confirmDisabled` holds the button until then. */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  text,
  confirm,
  busy,
  onConfirm,
  confirmDisabled = false,
  children,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: React.ReactNode
  text: React.ReactNode
  confirm: string
  busy: boolean
  onConfirm: () => void
  confirmDisabled?: boolean
  children?: React.ReactNode
}) {
  const common = useTranslations("common")

  return (
    <Dialog open={open} onOpenChange={(next) => !busy && onOpenChange(next)}>
      <DialogContent showCloseButton={false}>
        <DialogHeader className="gap-4">
          <DialogTitle className="no-dot mb-2">{title}</DialogTitle>
          <DialogDescription>{text}</DialogDescription>
        </DialogHeader>
        {children}
        <DialogFooter>
          <DialogClose
            render={
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={busy}
              />
            }
          >
            {common("keep")}
          </DialogClose>
          <Button
            variant="destructive"
            className="h-10 px-5 text-base"
            disabled={busy || confirmDisabled}
            onClick={onConfirm}
          >
            {confirm}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
