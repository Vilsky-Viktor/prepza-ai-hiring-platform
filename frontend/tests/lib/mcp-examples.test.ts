import { describe, expect, it } from "vitest"

import { MCP_EXAMPLES } from "@/config/mcp-docs"
import { mcpExamples } from "@/lib/mcp-examples"

describe("the MCP tab's example agents", () => {
  it("reads every example from its files, in both languages, each pinning its versions", async () => {
    const examples = await mcpExamples()

    expect(examples.map((example) => example.key)).toEqual(
      MCP_EXAMPLES.map((example) => example.key)
    )

    for (const { code } of examples) {
      const head = (text: string) => text.split("\n").slice(0, 2).join("\n")

      expect(head(code.python)).toMatch(/^# pip install .*==\d/m)
      expect(head(code.typescript)).toMatch(/^\/\/ npm install .*@\d/m)
    }
  })
})
