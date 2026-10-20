import { describe, expect, it } from "vitest"

import { LOCALES } from "@/constants/i18n"
import { paddleLocale } from "@/lib/paddle"

describe("Paddle's checkout language", () => {
  it("is the site's language where Paddle has it", () => {
    expect(paddleLocale("de")).toBe("de")
    expect(paddleLocale("ar")).toBe("ar")
    expect(paddleLocale("zh")).toBe("zh-Hans")
  })

  it("is English for a language Paddle hasn't", () => {
    for (const locale of [
      "et",
      "fa",
      "fil",
      "he",
      "hi",
      "id",
      "th",
      "uk",
      "vi",
    ]) {
      expect(paddleLocale(locale)).toBe("en")
    }
  })

  it("is one Paddle knows for every site language", () => {
    const paddle = [
      "en",
      "de",
      "es",
      "fr",
      "it",
      "ja",
      "ko",
      "nl",
      "sv",
      "no",
      "da",
      "pl",
      "pt",
      "ru",
      "zh-Hans",
      "zh-Hant",
      "ar",
      "tr",
    ]

    for (const locale of LOCALES) {
      expect(paddle).toContain(paddleLocale(locale))
    }
  })
})
