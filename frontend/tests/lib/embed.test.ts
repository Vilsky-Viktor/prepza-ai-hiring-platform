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

it("lets the company's allowed domains frame a guest invite", async () => {
  answers(
    Response.json({
      embed_ancestors: ["jobs.acme.com", "*.acme.com"],
    })
  )

  expect(await embedAncestors("tok")).toBe("jobs.acme.com *.acme.com")
})

it("asks with the page the frame says it's on and the one the browser came from", async () => {
  answers(Response.json({ embed_ancestors: [] }))

  await embedAncestors("tok", "https://jobs.acme.com", "https://jobs.acme.com/")

  const asked = new URL(
    vi.mocked(fetch).mock.calls[0][0] as string,
    "http://api"
  )
  expect(asked.searchParams.get("embed_origin")).toBe("https://jobs.acme.com")
  expect(asked.searchParams.get("embed_referrer")).toBe(
    "https://jobs.acme.com/"
  )
})

it("lets no one frame an invite without domains, an unknown one, or when unsure", async () => {
  answers(Response.json({ embed_ancestors: [] }))
  expect(await embedAncestors("tok")).toBe("'none'")

  answers(new Response(null, { status: 404 }))
  expect(await embedAncestors("tok")).toBe("'none'")

  answers(new Error("down"))
  expect(await embedAncestors("tok")).toBe("'none'")
})

it("puts nothing but frame-ancestors sources into the policy", async () => {
  answers(
    Response.json({
      embed_ancestors: [
        "https://acme.com; script-src *",
        "'unsafe-inline'",
        "http://localhost:3000",
        "https://[::1]:*",
      ],
    })
  )

  expect(await embedAncestors("tok")).toBe(
    "http://localhost:3000 https://[::1]:*"
  )
})

it("takes only a page's own origin to send messages to", () => {
  expect(originOf("https://jobs.acme.com")).toBe("https://jobs.acme.com")
  expect(originOf("https://jobs.acme.com/apply")).toBeNull()
  expect(originOf("*")).toBeNull()
  expect(originOf(["https://a.com", "https://b.com"])).toBeNull()
  expect(originOf(undefined)).toBeNull()
})
