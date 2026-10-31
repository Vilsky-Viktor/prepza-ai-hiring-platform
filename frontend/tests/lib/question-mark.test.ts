import { describe, expect, it } from "vitest"

import { endsWithQuestionMark } from "@/lib/question-mark"

describe("endsWithQuestionMark", () => {
  it("finds the question mark of every script", () => {
    expect(endsWithQuestionMark("More questions?")).toBe(true)
    expect(endsWithQuestionMark("还有问题？")).toBe(true)
    expect(endsWithQuestionMark("سؤال آخر؟")).toBe(true)
  })

  it("finds it before trailing spaces", () => {
    expect(endsWithQuestionMark("Why testee? ")).toBe(true)
  })

  it("leaves other titles alone, a question mark inside them too", () => {
    expect(endsWithQuestionMark("Automate your hiring")).toBe(false)
    expect(endsWithQuestionMark("Who? Them")).toBe(false)
    expect(endsWithQuestionMark("")).toBe(false)
  })
})
