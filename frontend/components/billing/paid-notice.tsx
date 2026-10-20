"use client"

import { useRouter } from "next/navigation"
import { CircleCheckBigIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { whenPaid, type PaidKind } from "@/lib/paddle"

// When to read the page again for the new balance after a payment, in seconds: Paddle's web hook
// usually lands within seconds, sometimes later.
const RECHECK_SECONDS = [2, 5, 10, 20, 40, 60]

/** A payment Paddle's checkout completed (it closes then): a large, centred dialog that the
 * payment went through, in place on the page the buyer is on, while the page reads its balance
 * again a few times so the new credits show up by themselves. */
export function PaidNotice() {
  const t = useTranslations("billing")
  const router = useRouter()
  const [paid, setPaid] = useState<PaidKind | null>(null)

  useEffect(() => whenPaid(setPaid), [])

  useEffect(() => {
    if (!paid) {
      return
    }

    const timers = RECHECK_SECONDS.map((seconds) =>
      window.setTimeout(() => router.refresh(), seconds * 1000)
    )

    return () => timers.forEach(clearTimeout)
  }, [paid, router])

  return (
    <Dialog
      open={paid !== null}
      onOpenChange={(open) => !open && setPaid(null)}
    >
      <DialogContent
        showCloseButton={false}
        className="sm:max-w-lg"
        data-testid="paid-notice"
        data-paid={paid ?? undefined}
      >
        <DialogHeader className="items-center gap-3 py-4 text-center">
          {/* A large green check that pops in as the dialog opens; still for reduced motion. */}
          <CircleCheckBigIcon
            aria-hidden
            strokeWidth={1.5}
            className="mb-2 size-24 animate-in text-emerald-600 duration-500 ease-out zoom-in-50 fade-in motion-reduce:animate-none dark:text-emerald-400"
          />
          <DialogTitle className="text-2xl">
            {paid === "auto_top_up" ? t("autoTopUpOnTitle") : t("paidTitle")}
          </DialogTitle>
          <DialogDescription className="max-w-sm text-base">
            {paid === "auto_top_up" ? t("autoTopUpOnText") : t("paidText")}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter showCloseButton />
      </DialogContent>
    </Dialog>
  )
}
