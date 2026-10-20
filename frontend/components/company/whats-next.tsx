"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useRef, useState, type ReactNode } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

/** Right after an interview is generated (the generation page marks the address with `ready`):
 * a dialog with what to do next, each step a button that takes the user there. Closing it takes
 * the mark off the address, so a reload doesn't show it again. */
export function WhatsNext({
  title,
  interviewHref,
}: {
  title: string
  interviewHref: string
}) {
  const t = useTranslations("interviews.whatsNext")
  const router = useRouter()
  const [open, setOpen] = useState(true)
  // Where the focus goes once the dialog closes: the first topic's question count, when asked.
  const focusAfter = useRef<HTMLElement | null>(null)

  function close() {
    setOpen(false)
    router.replace(interviewHref, { scroll: false })
  }

  function setLimits() {
    focusAfter.current = document.querySelector("[data-topic-limit]")
    close()
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !next && close()}>
      <DialogContent
        className="sm:max-w-lg"
        data-testid="whats-next"
        finalFocus={() => focusAfter.current ?? true}
      >
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>
            {t.rich("text", {
              title,
              name: (chunks) => (
                <span className="font-medium text-foreground">{chunks}</span>
              ),
            })}
          </DialogDescription>
        </DialogHeader>
        <ol className="list-decimal space-y-4 ps-5 text-base">
          <Step text={t("limits")}>
            <Button variant="outline" onClick={setLimits}>
              {t("limitsAction")}
            </Button>
          </Step>
          {/* When voice mode ships, choosing click or voice joins this step (in the settings). */}
          <Step text={t("time")}>
            <Button
              variant="outline"
              render={<Link href={`${interviewHref}?tab=settings`} />}
              nativeButton={false}
            >
              {t("timeAction")}
            </Button>
          </Step>
          <Step text={t("invite")}>
            <Button
              variant="outline"
              render={<Link href={`${interviewHref}?tab=candidates`} />}
              nativeButton={false}
            >
              {t("inviteAction")}
            </Button>
          </Step>
        </ol>
        <DialogFooter>
          <Button className="h-10 px-5 text-base" onClick={close}>
            {t("done")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/** One step: its line, with its button beside it (under it on phones). */
function Step({ text, children }: { text: string; children: ReactNode }) {
  return (
    <li>
      <div className="flex items-center justify-between gap-4 max-sm:flex-col max-sm:items-start max-sm:gap-2">
        <span>{text}</span>
        {children}
      </div>
    </li>
  )
}
