import {
  CheckoutEventNames,
  initializePaddle,
  type Paddle,
} from "@paddle/paddle-js"

import { PADDLE_FALLBACK_LOCALE, PADDLE_LOCALES } from "@/constants/paddle"
import type { Catalog } from "@/types/billing"

let paddle: Promise<Paddle | undefined> | null = null
let onCompleted: (() => void) | null = null

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
      if (event.name === CheckoutEventNames.CHECKOUT_COMPLETED) {
        onCompleted?.()
      }
    },
  })

  return paddle
}

/**
 * Opens Paddle's checkout: a top-up's transaction, which the backend made with whose wallet it
 * pays into, or the automatic top-up's price with the custom data the backend gave. What it
 * grants is decided by the backend from Paddle's price, once the payment has gone through. It
 * opens in the site's language (`locale`), or English where Paddle hasn't it.
 */
export async function openCheckout(
  catalog: Catalog,
  checkout:
    | { transactionId: string }
    | { priceId: string; customData: Record<string, string> },
  email: string | null,
  completed: () => void,
  locale: string
) {
  onCompleted = completed
  const instance = await load(catalog)

  instance?.Checkout.open({
    ...("transactionId" in checkout
      ? { transactionId: checkout.transactionId }
      : {
          items: [{ priceId: checkout.priceId, quantity: 1 }],
          customData: checkout.customData,
        }),
    ...(email ? { customer: { email } } : {}),
    // No discount codes are issued for now, so checkout doesn't offer to enter one.
    settings: { showAddDiscounts: false, locale: paddleLocale(locale) },
  })
}
