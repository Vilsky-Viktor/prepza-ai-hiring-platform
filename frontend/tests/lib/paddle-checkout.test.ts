import { beforeEach, describe, expect, it, vi } from "vitest"

import type { Catalog } from "@/types/billing"

// A stand-in for Paddle.js: it keeps the event callback the site sets and records the checkout.
const fake = vi.hoisted(() => ({
  callback: null as null | ((event: object) => void),
  open: vi.fn(),
  close: vi.fn(),
}))

vi.mock("@paddle/paddle-js", async (actual) => ({
  ...(await actual<typeof import("@paddle/paddle-js")>()),
  initializePaddle: vi.fn(
    async (options: { eventCallback: (event: object) => void }) => {
      fake.callback = options.eventCallback

      return { Checkout: { open: fake.open, close: fake.close } }
    }
  ),
}))

const catalog = { environment: "sandbox", client_token: "test" } as Catalog

async function opened(paid: "top_up" | "auto_top_up") {
  const paddle = await import("@/lib/paddle")
  const handler = vi.fn()
  paddle.whenPaid(handler)
  await paddle.openCheckout({
    catalog,
    checkout: { transactionId: "txn_1" },
    email: "owner@example.com",
    theme: "dark",
    paid,
    locale: "de",
  })

  return handler
}

describe("Paddle's checkout", () => {
  beforeEach(() => {
    vi.resetModules()
    fake.open.mockClear()
    fake.close.mockClear()
  })

  it("opens in the site's theme and language, on the page, with no address to come back to", async () => {
    await opened("top_up")

    const settings = fake.open.mock.calls[0][0].settings
    expect(settings).toMatchObject({ theme: "dark", locale: "de" })
    expect(settings).not.toHaveProperty("successUrl")
    expect(fake.open.mock.calls[0][0].transactionId).toBe("txn_1")
  })

  it("closes and tells the success dialog what was paid for once the payment completes", async () => {
    const handler = await opened("auto_top_up")

    fake.callback?.({ name: "checkout.completed", data: {} })
    await vi.waitFor(() => expect(fake.close).toHaveBeenCalled())

    expect(handler).toHaveBeenCalledExactlyOnceWith("auto_top_up")
  })

  it("tells of one payment once, however often Paddle reports it", async () => {
    const handler = await opened("top_up")

    fake.callback?.({ name: "checkout.completed", data: {} })
    fake.callback?.({ name: "checkout.completed", data: {} })

    expect(handler).toHaveBeenCalledExactlyOnceWith("top_up")
  })

  it("tells nothing of a checkout that didn't complete", async () => {
    const handler = await opened("top_up")

    fake.callback?.({ name: "checkout.closed", data: {} })

    expect(handler).not.toHaveBeenCalled()
  })
})
