import { describe, expect, it } from "vitest"

import { isLocale, preferredLocale, textDirection } from "@/lib/locale"

describe("isLocale", () => {
  it("knows the supported languages only", () => {
    expect(isLocale("en")).toBe(true)
    expect(isLocale("fil")).toBe(true)
    expect(isLocale("xx")).toBe(false)
    expect(isLocale("EN")).toBe(false)
  })
})

describe("textDirection", () => {
  it("writes Arabic, Hebrew and Persian right to left", () => {
    expect(textDirection("ar")).toBe("rtl")
    expect(textDirection("he")).toBe("rtl")
    expect(textDirection("fa")).toBe("rtl")
  })

  it("writes the other languages left to right", () => {
    expect(textDirection("en")).toBe("ltr")
    expect(textDirection("ja")).toBe("ltr")
  })
})

describe("preferredLocale", () => {
  it("takes the first supported language by preference", () => {
    expect(preferredLocale("uk-UA,ru;q=0.8")).toBe("uk")
    expect(preferredLocale("ru;q=0.5, de;q=0.9")).toBe("de")
  })

  it("skips languages that aren't supported", () => {
    expect(preferredLocale("xx-YY, sv;q=0.9, fr;q=0.8")).toBe("fr")
  })

  it("leaves out languages asked with quality 0", () => {
    expect(preferredLocale("de;q=0, es;q=0.1")).toBe("es")
  })

  it("never gives Traditional Chinese the Simplified", () => {
    expect(preferredLocale("zh-TW,zh;q=0.9")).toBe("zh")
    expect(preferredLocale("zh-TW, ja;q=0.5")).toBe("ja")
    expect(preferredLocale("zh-Hant-HK")).toBeUndefined()
    expect(preferredLocale("zh-CN")).toBe("zh")
  })

  it("reads region and case alike", () => {
    expect(preferredLocale("PT-br")).toBe("pt")
  })

  it("gives none for no header or no supported language", () => {
    expect(preferredLocale(null)).toBeUndefined()
    expect(preferredLocale("")).toBeUndefined()
    expect(preferredLocale("sv, *;q=0.1")).toBeUndefined()
  })
})
