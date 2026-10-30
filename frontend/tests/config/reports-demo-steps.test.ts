import { describe, expect, it } from "vitest"

import { REPORT_TARGETS, reportSteps } from "@/config/reports-demo-steps"

const LINES: [string, string] = ["looks the best", "cheating"]
const STEPS = reportSteps(0, 1, LINES, "lisa@example.com", "Proceeding")
const names = STEPS.map((step) => step.name)

describe("reportSteps", () => {
  it("plays the list, both candidates' pages, the notes and Slack, in that order", () => {
    const order = [
      "download",
      "share",
      "share0",
      "share1",
      "post",
      "slack",
    ].map((name) => names.indexOf(name))

    expect(order.every((at) => at >= 0)).toBe(true)
    expect(order).toEqual([...order].sort((a, b) => a - b))
    // It rests on the Slack channel scrolled to its newest message.
    expect(names.at(-1)).toBe("slackScrolled")
  })

  it("types each text a letter a step", () => {
    const repeat = (name: string) =>
      STEPS.find((step) => step.name === name)?.repeat

    expect(repeat("typingEmail")).toBe("lisa@example.com".length)
    expect(repeat("typing0")).toBe(LINES[0].length)
    expect(repeat("typing1")).toBe(LINES[1].length)
    expect(repeat("typingNote")).toBe("Proceeding".length)
  })

  it("opens each shared candidate's page from their row", () => {
    expect(STEPS.find((step) => step.name === "page0")?.candidate).toBe(0)
    expect(STEPS.find((step) => step.name === "page1")?.candidate).toBe(1)
  })

  it("points only at targets the demo knows", () => {
    const points = STEPS.flatMap((step) =>
      step.point && step.point !== "none" ? [step.point] : []
    )

    expect(points.filter((point) => !REPORT_TARGETS.includes(point))).toEqual(
      []
    )
  })

  it("names every step once", () => {
    expect(new Set(names).size).toBe(names.length)
  })
})
