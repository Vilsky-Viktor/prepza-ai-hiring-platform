import {
  CheckoutEventNames,
  initializePaddle,
  type Paddle,
} from "@paddle/paddle-js"

import { PADDLE_FALLBACK_LOCALE, PADDLE_LOCALES } from "@/constants/paddle"
import type { Catalog } from "@/types/billing"

let paddle: Promise<Paddle | undefined> | null = null

// What a checkout pays for: a top-up, or the card that turns automatic top-up on. The success
// dialog (components/billing/paid-notice.tsx) says which.
export type PaidKind = "top_up" | "auto_top_up"

export type CheckoutOptions = {
  catalog: Catalog
  // A top-up's transaction, or the automatic top-up's price with its custom data.
  checkout:
    | { transactionId: string }
    | { priceId: string; customData: Record<string, string> }
  email: string | null
  theme: "light" | "dark"
  paid: PaidKind
  locale: string
}

// The checkout open now, and who's told when its payment completes (the success dialog,
// components/billing/paid-notice.tsx).
let opened: CheckoutOptions | null = null
let onPaid: ((paid: PaidKind) => void) | null = null

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

/** The language Paddle's checkout opens in for the site's `locale`: the same, or English. */
export function paddleLocale(locale: string) {
  return PADDLE_LOCALES[locale] ?? PADDLE_FALLBACK_LOCALE
}

/** Paddle.js, loaded once on the first purchase. */
function load(catalog: Catalog) {
  paddle ??= initializePaddle({
    environment:
      catalog.environment === "production" ? "production" : "sandbox",
    token: catalog.client_token,
    eventCallback: (event) => {
      // Paid: the checkout closes and the success dialog shows on the page, once per checkout.
      if (event.name === CheckoutEventNames.CHECKOUT_COMPLETED && opened) {
        const { paid } = opened
        opened = null
        void closeCheckout()
        onPaid?.(paid)
      }
    },
  })

  return paddle
}

/**
 * Opens Paddle's checkout: a top-up's transaction, which the backend made with whose wallet it
 * pays into, or the automatic top-up's price with the custom data the backend gave. What it
 * grants is decided by the backend from Paddle's price, once the payment has gone through. It
 * follows the site's light or dark theme and language (`locale`, English where Paddle hasn't
 * it). The buyer stays on the page: a completed payment is told to `whenPaid`, with what it
 * paid for (`paid`).
 */
export async function openCheckout(options: CheckoutOptions) {
  const { catalog, checkout, email, theme, locale } = options
  const instance = await load(catalog)
  opened = options

  instance?.Checkout.open({
    ...("transactionId" in checkout
      ? { transactionId: checkout.transactionId }
      : {
          items: [{ priceId: checkout.priceId, quantity: 1 }],
          customData: checkout.customData,
        }),
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

/** Closes the checkout, so our success dialog shows instead of it. */
async function closeCheckout() {
  ;(await paddle)?.Checkout.close()
}
