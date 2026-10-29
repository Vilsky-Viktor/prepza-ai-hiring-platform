import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { newsPosts } from "@/lib/news-posts"

vi.mock("next/headers", () => ({ cookies: async () => ({ get: () => null }) }))
vi.mock("next-intl/server", () => ({ getLocale: async () => "de" }))

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockResolvedValue(Response.json([]))
  vi.stubGlobal("fetch", fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  fetchMock.mockReset()
})

describe("newsPosts", () => {
  it("asks the API every time, so a deleted post leaves the page at once", async () => {
    expect(await newsPosts(0, 20)).toEqual([])

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toMatch(/\/api\/site\/news\?offset=0&limit=20$/)
    expect(init.cache).toBe("no-store")
    expect(init.next).toBeUndefined()
    expect(init.headers).toEqual({ "Accept-Language": "de" })
  })

  it("asks in the language named", async () => {
    await newsPosts(0, 50, "fr")

    expect(fetchMock.mock.calls[0][1].headers).toEqual({
      "Accept-Language": "fr",
    })
  })
})
