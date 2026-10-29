import { readdirSync, readFileSync } from "node:fs"
import path from "node:path"

import { describe, expect, it } from "vitest"

import { SOURCE_ROOT } from "../source-files"

// proxy.ts's matcher is read from its file, as Next.js does: it must stay a plain string there.
const PROXY = readFileSync(path.join(SOURCE_ROOT, "proxy.ts"), "utf8")
const SOURCE = /source:\s*"([^"]+)"/.exec(PROXY)![1]
const matched = (path: string) => new RegExp(`^${SOURCE}$`).test(path)

describe("the proxy's matcher", () => {
  it("leaves out every file and folder in public/", () => {
    const entries = readdirSync(new URL("../../public", import.meta.url), {
      withFileTypes: true,
    }).filter((entry) => !entry.name.startsWith("."))

    expect(entries.length).toBeGreaterThan(0)

    for (const entry of entries) {
      const path = entry.isDirectory()
        ? `/${entry.name}/file.png`
        : `/${entry.name}`

      expect(matched(path), path).toBe(false)
    }
  })

  it("leaves out Next's files and the API, and runs on pages", () => {
    expect(matched("/_next/static/chunks/main.js")).toBe(false)
    expect(matched("/api/accounts/me")).toBe(false)

    for (const page of ["/", "/about", "/documents", "/de/about", "/api-docs"]) {
      expect(matched(page), page).toBe(true)
    }
  })
})
