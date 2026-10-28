import { describe, expect, it } from "vitest"

import { LOCALES } from "@/config/i18n"
import { englishLanguageName } from "@/lib/english-language-name"

describe("englishLanguageName", () => {
  it("names each language in English, Chinese by its script", () => {
    expect(englishLanguageName("ar")).toBe("Arabic")
    expect(englishLanguageName("de")).toBe("German")
    expect(englishLanguageName("zh")).toBe("Chinese (Simplified)")
    expect(englishLanguageName("fil")).toBe("Filipino")
  })

  it("has a distinct name for every language the site has", () => {
    const names = LOCALES.map(englishLanguageName)

    expect(new Set(names).size).toBe(LOCALES.length)
    expect(names.every((name, index) => name !== LOCALES[index])).toBe(true)
  })
})
