import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ApiError } from "@/lib/api"
import { downloadFile } from "@/lib/download"

vi.mock("@/lib/api", async (original) => ({
  ...(await original<typeof import("@/lib/api")>()),
  authHeaders: async () => ({ Authorization: "Bearer token" }),
}))

let calls: [string, RequestInit][]
let saved: { href: string; download: string }[]

function replying(response: () => Response) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init: RequestInit) => {
      calls.push([url, init])

      return response()
    })
  )
}

beforeEach(() => {
  calls = []
  saved = []
  vi.spyOn(URL, "createObjectURL").mockImplementation(() => "blob:file")
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined)
  vi.stubGlobal("document", {
    createElement: () => {
      const link = {
        href: "",
        download: "",
        click: () => saved.push({ href: link.href, download: link.download }),
      }

      return link
    },
  })
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe("downloadFile", () => {
  it("saves the file signed in, under the name the API gives it", async () => {
    replying(
      () =>
        new Response("candidate_id\n", {
          headers: {
            "Content-Disposition":
              'attachment; filename="testee-bias-audit-2026-10-30.csv"',
          },
        })
    )

    await downloadFile("/companies/companies/c-1/bias-audit?interview_id=i-1")

    expect(calls[0][0]).toBe(
      "/api/companies/companies/c-1/bias-audit?interview_id=i-1"
    )
    expect(calls[0][1].headers).toEqual({ Authorization: "Bearer token" })
    expect(saved).toEqual([
      { href: "blob:file", download: "testee-bias-audit-2026-10-30.csv" },
    ])
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:file")
  })

  it("fails with the service's message and saves nothing", async () => {
    replying(() =>
      Response.json(
        { detail: "Too many requests. Try again later." },
        { status: 429 }
      )
    )

    const refused = downloadFile("/companies/companies/c-1/bias-audit")

    await expect(refused).rejects.toBeInstanceOf(ApiError)
    await expect(refused).rejects.toMatchObject({
      status: 429,
      message: "Too many requests. Try again later.",
      fromService: true,
    })
    expect(saved).toEqual([])
  })
})
