import { describe, expect, it } from "vitest"

import { AI_CHIP_MASK } from "@/constants/ai-mark"

describe("AI_CHIP_MASK", () => {
  it("is a CSS url of an SVG image drawing the chip's body and pins", () => {
    const svg = decodeURIComponent(
      AI_CHIP_MASK.replace(/^url\("data:image\/svg\+xml,/, "").replace(
        /"\)$/,
        ""
      )
    )

    expect(AI_CHIP_MASK).toMatch(/^url\("data:image\/svg\+xml,.+"\)$/)
    expect(svg).toContain('viewBox="0 0 24 24"')
    expect(svg).toContain("<rect")
    expect(svg.match(/<path /g)).toHaveLength(15)
  })
})
