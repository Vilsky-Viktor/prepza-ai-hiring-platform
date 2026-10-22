import { describe, expect, it } from "vitest"

import { keptCaseParts } from "@/lib/keep-case"

// The words each text keeps as written.
const kept = (text: string) =>
  keptCaseParts(text).filter((_, index) => index % 2)

describe("keptCaseParts", () => {
  it("keeps acronyms and Slack, in any script", () => {
    expect(kept("Connect your ATS and Slack")).toEqual(["ATS", "Slack"])
    expect(kept("Здравствуйте, я Мира, ваш ИИ-ассистент")).toEqual([
      "Мира",
      "ИИ",
    ])
  })

  it("keeps Mira's name in the forms the languages use", () => {
    expect(kept("ask Mira")).toEqual(["Mira"])
    expect(kept("küsi Miralt")).toEqual(["Miralt"])
    expect(kept("zapytaj Mirę")).toEqual(["Mirę"])
    expect(kept("Mira'ya sor")).toEqual(["Mira"])
    expect(kept("спросить Миру")).toEqual(["Миру"])
    expect(kept("запитати Міру")).toEqual(["Міру"])
  })

  it("leaves words that only start like them", () => {
    expect(kept("Miracle Mirror Миротворец ATSs")).toEqual([])
    expect(kept("a single A")).toEqual([])
  })

  it("puts the parts back together as they were", () => {
    const text = "Hi, I'm Mira, your AI assistant"

    expect(keptCaseParts(text).join("")).toBe(text)
  })
})
