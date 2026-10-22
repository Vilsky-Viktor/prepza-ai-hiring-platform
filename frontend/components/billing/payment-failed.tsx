"use client"

import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import { OutcomeDialog } from "@/components/billing/outcome-dialog"
import { Button } from "@/components/ui/button"
import { PAYMENT_FAILURE_TIMEOUT_MS } from "@/constants/paddle"
import { apiFetch } from "@/lib/api"
import { hasMessage } from "@/lib/messages"
import {
  closeCheckout,
  reopenCheckout,
  stillLatest,
  whenPaymentFails,
  type PaymentFailure,
} from "@/lib/paddle"
import type { PaymentFailureData } from "@/types/billing"

// Billing's answer when it can't tell why; also used for a key the messages don't have.
const OTHER = "other"

/** A payment that failed in Paddle's checkout (a declined card, a failed wallet payment and so
 * on): once billing says why, the checkout closes and this dialog says what the buyer can do,
 * with a button that opens the same checkout again for another card or payment method. While
 * billing answers, Paddle's own checkout shows its error. */
export function PaymentFailed() {
  const t = useTranslations("billing")
  const [failure, setFailure] = useState<PaymentFailure | null>(null)
  const [reason, setReason] = useState(OTHER)

  useEffect(
    () =>
      whenPaymentFails(async (found) => {
        const query = new URLSearchParams({
          transaction_id: found.transactionId,
        })
        const path = `/companies/companies/${found.companyId}/billing/payment-failure?${query}`
        const answer = await apiFetch<PaymentFailureData>(path, {
          signal: AbortSignal.timeout(PAYMENT_FAILURE_TIMEOUT_MS),
        }).catch(() => null)

        // The buyer tried again in the checkout meanwhile.
        if (!stillLatest(found)) {
          return
        }

        await closeCheckout()
        setReason(answer?.reason ?? OTHER)
        setFailure(found)
      }),
    []
  )

  const key = `paymentFailed.${reason}` as const

  function tryAgain() {
    if (!failure) {
      return
    }

    // This dialog closes first, so the checkout isn't opened under it.
    setFailure(null)
    void reopenCheckout(failure.transactionId)
  }

  return (
    <OutcomeDialog
      open={failure !== null}
      onClose={() => setFailure(null)}
      tone="failure"
      title={t("paymentFailedTitle")}
      description={t(hasMessage(t, key) ? key : `paymentFailed.${OTHER}`)}
      action={<Button onClick={tryAgain}>{t("tryAnotherMethod")}</Button>}
      data-testid="payment-failed"
      data-reason={failure ? reason : undefined}
    />
  )
}
