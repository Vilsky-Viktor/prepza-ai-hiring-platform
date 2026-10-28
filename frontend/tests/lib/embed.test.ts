import { afterEach, expect, it, vi } from "vitest"

import { EMBED_PAGE } from "@/config/embed"
import { embedAncestors, originOf } from "@/lib/embed"

afterEach(() => {
  vi.unstubAllGlobals()
})

function answers(response: Response | Error) {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      response instanceof Error
        ? Promise.reject(response)
        : Promise.resolve(response)
    )
  )
}

it("finds the invite's token in the embedded page's address, in any language", () => {
  expect(EMBED_PAGE.exec("/embedded/tok-1")?.[1]).toBe("tok-1")
  expect(EMBED_PAGE.exec("/de/embedded/tok-1")?.[1]).toBe("tok-1")
  expect(EMBED_PAGE.exec("/embed/v1.js")).toBeNull()
})

it("lets the company's domain and its subdomains frame a guest invite", async () => {
  answers(Response.json({ embed_domain: "acme.com" }))

  expect(await embedAncestors("tok")).toBe("acme.com *.acme.com")
})

it("lets no one frame an invite without a domain, an unknown one, or when unsure", async () => {
  answers(Response.json({ embed_domain: null }))
  expect(await embedAncestors("tok")).toBe("'none'")

  answers(new Response(null, { status: 404 }))
  expect(await embedAncestors("tok")).toBe("'none'")

  answers(new Error("down"))
  expect(await embedAncestors("tok")).toBe("'none'")
})

it("takes only a page's own origin to send messages to", () => {
  expect(originOf("https://jobs.acme.com")).toBe("https://jobs.acme.com")
  expect(originOf("https://jobs.acme.com/apply")).toBeNull()
  expect(originOf("*")).toBeNull()
  expect(originOf(["https://a.com", "https://b.com"])).toBeNull()
  expect(originOf(undefined)).toBeNull()
})
