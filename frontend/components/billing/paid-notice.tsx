"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import { OutcomeDialog } from "@/components/billing/outcome-dialog"
import { whenPaid, type PaidKind } from "@/lib/paddle"

// When to read the page again for the new balance after a payment, in seconds: Paddle's web hook
// usually lands within seconds, sometimes later.
const RECHECK_SECONDS = [2, 5, 10, 20, 40, 60]

/** A payment Paddle's checkout completed (it closes then): a dialog that the payment went
 * through, in place on the page the buyer is on, while the page reads its balance again a few
 * times so the new credits show up by themselves. */
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
    <OutcomeDialog
      open={paid !== null}
      onClose={() => setPaid(null)}
      tone="success"
      title={paid === "auto_top_up" ? t("autoTopUpOnTitle") : t("paidTitle")}
      description={
        paid === "auto_top_up" ? t("autoTopUpOnText") : t("paidText")
      }
      data-testid="paid-notice"
      data-paid={paid ?? undefined}
    />
  )
}
