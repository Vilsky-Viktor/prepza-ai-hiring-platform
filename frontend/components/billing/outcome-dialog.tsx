"use client"

import { cn } from "cn"
import { CircleCheckBigIcon, CircleOffIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import type { ComponentProps, ReactNode } from "react"

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

// The large icon over the title: a green check for a success, a struck-through circle in the
// destructive colour for a failure.
const TONES = {
  success: {
    Icon: CircleCheckBigIcon,
    icon: "text-emerald-600 dark:text-emerald-400",
  },
  failure: { Icon: CircleOffIcon, icon: "text-destructive" },
}

/** How a payment ended: a large dialog, centred, with the outcome's icon over its title and
 * text, and in the footer Close, before the `action` when there's one. The rest of the props (a test id, a state
 * attribute) go on the dialog itself. */
export function OutcomeDialog({
  open,
  onClose,
  tone,
  title,
  description,
  action,
  ...props
}: {
  open: boolean
  onClose: () => void
  tone: keyof typeof TONES
  title: ReactNode
  description: ReactNode
  action?: ReactNode
} & Omit<ComponentProps<typeof DialogContent>, "title">) {
  const t = useTranslations("common")
  const { Icon, icon } = TONES[tone]

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent showCloseButton={false} className="sm:max-w-lg" {...props}>
        <DialogHeader className="items-center gap-3 py-4 text-center">
          {/* Pops in as the dialog opens; still for reduced motion. */}
          <Icon
            aria-hidden
            strokeWidth={1.5}
            className={cn(
              "mb-2 size-24 animate-in duration-500 ease-out zoom-in-50 fade-in motion-reduce:animate-none",
              icon
            )}
          />
          <DialogTitle className="text-2xl">{title}</DialogTitle>
          <DialogDescription className="max-w-sm text-base">
            {description}
          </DialogDescription>
        </DialogHeader>
        {action ? (
          <DialogFooter>
            <DialogClose render={<Button variant="outline" />}>
              {t("close")}
            </DialogClose>
            {action}
          </DialogFooter>
        ) : (
          <DialogFooter showCloseButton />
        )}
      </DialogContent>
    </Dialog>
  )
}
