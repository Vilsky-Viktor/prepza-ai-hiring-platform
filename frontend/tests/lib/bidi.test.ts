import { describe, expect, it } from "vitest"

import { bdiText, withoutIsolates } from "@/lib/bidi"

describe("bdiText", () => {
  it("isolates a value between first strong isolate and pop directional isolate", () => {
    expect(bdiText.bdi("أكمي")).toBe("\u2068أكمي\u2069")
  })
})

describe("withoutIsolates", () => {
  it("takes out the marks bdiText adds and keeps the text", () => {
    expect(withoutIsolates(`Test ${bdiText.bdi("أكمي")}`)).toBe("Test أكمي")
  })
})
