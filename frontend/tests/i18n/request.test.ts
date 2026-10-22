import { afterEach, describe, expect, it, vi } from "vitest"

const captureException = vi.fn()

vi.mock("@sentry/nextjs", () => ({ captureException }))
vi.mock("next/headers", () => ({
  headers: async () => new Headers({ "accept-language": "de" }),
  cookies: async () => ({ get: () => undefined }),
}))
vi.mock("next-intl/server", () => ({
  getRequestConfig: (make: unknown) => make,
}))

afterEach(() => {
  captureException.mockReset()
})

describe("the request's message config", () => {
  it("reports a message that can't be shown", async () => {
    const { default: config } = await import("@/i18n/request")
    const made = await (
      config as unknown as () => Promise<{ onError: (error: Error) => void }>
    )()
    const error = new Error("MISSING_MESSAGE: billing.nope")

    made.onError(error)

    expect(captureException).toHaveBeenCalledWith(error)
  })
})
