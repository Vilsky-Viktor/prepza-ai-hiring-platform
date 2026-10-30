import { describe, expect, it } from "vitest"

import { candidatesPath, interviewTab } from "@/lib/interview-page"

describe("candidatesPath", () => {
  it("asks for the candidates by sort, with the search and status only when set", () => {
    expect(candidatesPath("i1", "date", "", null)).toBe(
      "/companies/interviews/i1/candidates?sort=date"
    )
    expect(candidatesPath("i1", "grade", "ann", "finished")).toBe(
      "/companies/interviews/i1/candidates?sort=grade&q=ann&status=finished"
    )
  })
})

describe("interviewTab", () => {
  it("shows the tab asked for once the interview is ready", () => {
    expect(interviewTab("candidates", true, false)).toBe("candidates")
    expect(interviewTab("settings", true, true)).toBe("settings")
    expect(interviewTab("notes", true, false)).toBe("notes")
  })

  it("shows the topics while generating, for an unknown tab, and settings to viewers", () => {
    expect(interviewTab("candidates", false, true)).toBe("topics")
    expect(interviewTab("notes", false, true)).toBe("topics")
    expect(interviewTab("nope", true, true)).toBe("topics")
    expect(interviewTab("settings", true, false)).toBe("topics")
    expect(interviewTab(undefined, true, true)).toBe("topics")
  })

  it("shows Discover only to a company the API allows it", () => {
    expect(interviewTab("discover", true, false, true)).toBe("discover")
    expect(interviewTab("discover", true, true, false)).toBe("topics")
    expect(interviewTab("discover", false, true, true)).toBe("topics")
  })
})
