import type { Paddle } from "@paddle/paddle-js"

import { PADDLE_FALLBACK_LOCALE, PADDLE_LOCALES } from "@/constants/paddle"
import type { Catalog } from "@/types/billing"

let paddle: Promise<Paddle | undefined> | null = null

// What a checkout pays for: a top-up, the card that turns automatic top-up on, or a new card
// for it. The success dialog (components/billing/paid-notice.tsx) says which.
export type PaidKind = "top_up" | "auto_top_up" | "card"

export type CheckoutOptions = {
  catalog: Catalog
  // The transaction billing made: a top-up's, or the one that saves the card for automatic
  // top-up, in the company's currency.
  checkout: { transactionId: string }
  email: string | null
  theme: "light" | "dark"
  paid: PaidKind
  locale: string
  // The company it pays into, whose billing says why a payment failed.
  companyId: string
}

/** A payment that failed in the checkout: its transaction, the company it was for, and which
 * payment attempt it was. */
export type PaymentFailure = {
  companyId: string
  transactionId: string
  attempt: number
}

// The checkout open now, to open it again after a failed payment; and who's told when a payment
// completes (the success dialog, components/billing/paid-notice.tsx) or fails (the failure
// dialog, components/billing/payment-failed.tsx).
let opened: CheckoutOptions | null = null
let onPaid: ((paid: PaidKind) => void) | null = null
let onFailed: ((failure: PaymentFailure) => void) | null = null
// Counts the payment attempts, so a failure the buyer has already retried past is left alone.
let attempt = 0

/** Whether `failure` is still the latest payment attempt. */
export function stillLatest(failure: PaymentFailure) {
  return failure.attempt === attempt
}

/** Tells `handler` when the checkout completes a payment, with what it paid for; returns what
 * stops it. */
export function whenPaid(handler: (paid: PaidKind) => void) {
  onPaid = handler

  return () => {
    if (onPaid === handler) {
      onPaid = null
    }
  }
}

/** Tells `handler` when a payment fails in the checkout; returns what stops it. */
export function whenPaymentFails(handler: (failure: PaymentFailure) => void) {
  onFailed = handler

  return () => {
    if (onFailed === handler) {
      onFailed = null
    }
  }
}

/** The language Paddle's checkout opens in for the site's `locale`: the same, or English. */
export function paddleLocale(locale: string) {
  return PADDLE_LOCALES[locale] ?? PADDLE_FALLBACK_LOCALE
}

/** Paddle.js, loaded once on the first purchase; its loader too, so no other page carries it
 * (the paid and failed dialogs, in the root layout, import this file). */
function load(catalog: Catalog) {
  paddle ??= import("@paddle/paddle-js").then(
    ({ CheckoutEventNames, initializePaddle }) =>
      initializePaddle({
        environment:
          catalog.environment === "production" ? "production" : "sandbox",
        token: catalog.client_token,
        eventCallback: (event) => {
          const transactionId = event.data?.transaction_id

          if (event.name === CheckoutEventNames.CHECKOUT_PAYMENT_INITIATED) {
            attempt += 1
          }

          // Paid: the checkout closes and the success dialog shows on the page, once per
          // checkout.
          if (event.name === CheckoutEventNames.CHECKOUT_COMPLETED && opened) {
            const { paid } = opened
            opened = null
            void closeCheckout()
            onPaid?.(paid)
          }

          if (
            event.name === CheckoutEventNames.CHECKOUT_PAYMENT_FAILED &&
            opened &&
            transactionId
          ) {
            onFailed?.({ companyId: opened.companyId, transactionId, attempt })
          }
        },
      })
  )

  return paddle
}

/**
 * Opens Paddle's checkout on a transaction the backend made, with whose wallet it pays into and
 * its currency: a top-up's, or the one that saves the card for automatic top-up. What it grants
 * is decided by the backend from the price it made, once the payment has gone through. It
 * follows the site's light or dark theme and language (`locale`, English where Paddle hasn't
 * it). The buyer stays on the page: a completed payment is told to `whenPaid`, with what it
 * paid for (`paid`), and a failed one to `whenPaymentFails`.
 */
export async function openCheckout(options: CheckoutOptions) {
  const { catalog, checkout, email, theme, locale } = options
  const instance = await load(catalog)
  opened = options

  instance?.Checkout.open({
    transactionId: checkout.transactionId,
    ...(email ? { customer: { email } } : {}),
    // No discount codes are issued for now, so checkout doesn't offer to enter one.
    settings: {
      showAddDiscounts: false,
      variant: "one-page",
      theme,
      locale: paddleLocale(locale),
    },
  })
}

/** Closes the checkout, so our success or failure dialog shows instead of it. */
export async function closeCheckout() {
  ;(await paddle)?.Checkout.close()
}

/** Opens the failed payment's checkout again (its transaction keeps what it buys and the
 * custom data), for another card or payment method. */
export async function reopenCheckout(transactionId: string) {
  if (opened) {
    await openCheckout({ ...opened, checkout: { transactionId } })
  }
}
