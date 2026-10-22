import { describe, expect, it, vi } from "vitest"

import type { Catalog } from "@/types/billing"

// Whether Paddle's loader package was imported: the paid and failed dialogs import lib/paddle on
// every page (the root layout), so the package must wait for the first purchase.
const loaded = vi.hoisted(() => ({ count: 0 }))

vi.mock("@paddle/paddle-js", async (actual) => {
  loaded.count += 1

  return {
    ...(await actual<typeof import("@paddle/paddle-js")>()),
    initializePaddle: vi.fn(async () => ({
      Checkout: { open: vi.fn(), close: vi.fn() },
    })),
  }
})

describe("Paddle's loader", () => {
  it("is imported on the first purchase, not with the page", async () => {
    vi.resetModules()
    const paddle = await import("@/lib/paddle")
    paddle.whenPaid(vi.fn())
    paddle.whenPaymentFails(vi.fn())

    expect(loaded.count).toBe(0)

    await paddle.openCheckout({
      catalog: { environment: "sandbox", client_token: "test" } as Catalog,
      checkout: { transactionId: "txn_1" },
      email: null,
      theme: "light",
      paid: "top_up",
      locale: "en",
      companyId: "company-1",
    })

    expect(loaded.count).toBe(1)
  })
})
