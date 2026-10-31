import { afterEach, expect, it, vi } from "vitest"

import { openAddress, safeToOpen } from "@/lib/navigation"

afterEach(() => {
  vi.unstubAllGlobals()
})

it("opens pages and desktop apps' own addresses", () => {
  expect(safeToOpen("https://claude.ai/api/mcp/auth_callback?code=x")).toBe(
    true
  )
  expect(safeToOpen("http://127.0.0.1:33418/callback")).toBe(true)
  expect(safeToOpen("cursor://anysphere.cursor-mcp/oauth/callback")).toBe(true)
})

it("never opens an address that runs in the page, or one that isn't an address", () => {
  for (const url of [
    "javascript:alert(1)",
    " JavaScript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "vbscript:msgbox",
    "blob:https://testee.ai/x",
    "/relative",
    null,
  ]) {
    expect(safeToOpen(url)).toBe(false)
  }
})

it("goes to a safe address and refuses the rest", () => {
  const assign = vi.fn()
  vi.stubGlobal("window", { location: { assign } })

  openAddress("https://checkout.paddle.com/invoice/1")
  expect(() => openAddress("javascript:alert(1)")).toThrow()
  expect(assign).toHaveBeenCalledTimes(1)
})
