import { describe, expect, it } from "vitest"

import { codeTokens, editorText, questionCodeColors } from "@/lib/code-tokens"

describe("codeTokens", () => {
  it("colors each line's tokens for both themes", async () => {
    const lines = await codeTokens('print("hi")\nx = 1', "python")

    expect(lines).toHaveLength(2)
    expect(lines![0].map((token) => token.content).join("")).toBe('print("hi")')
    expect(lines![0][0].style).toHaveProperty("--shiki-light")
    expect(lines![0][0].style).toHaveProperty("--shiki-dark")
  })

  it("leaves code plain without a language or in one it doesn't know", async () => {
    expect(await codeTokens("x = 1")).toBeNull()
    expect(await codeTokens("x = 1", "no-such-language")).toBeNull()
  })
})

describe("editorText", () => {
  it("drops the last new lines, which would show as empty lines", () => {
    expect(editorText("a\nb\n\n")).toBe("a\nb")
  })
})

describe("questionCodeColors", () => {
  it("colors a question's code blocks in order", async () => {
    const colors = await questionCodeColors(
      "What prints?\n```python\nprint(1)\n```\nAnd here?\n```sql\nSELECT 1\n```"
    )

    expect(colors).toHaveLength(2)
    expect(colors[0]![0].map((token) => token.content).join("")).toBe(
      "print(1)"
    )
    expect(colors[1]![0].map((token) => token.content).join("")).toBe(
      "SELECT 1"
    )
  })
})
