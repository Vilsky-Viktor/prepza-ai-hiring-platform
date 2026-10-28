import { createTranslator } from "next-intl"
import { describe, expect, it } from "vitest"

import fil from "../../messages/fil.json"

// Filipino's `one` form covers 3 as well, so the free candidates' plural must use `=1` to show "3".
describe("Filipino free candidates", () => {
  const t = createTranslator({ locale: "fil", messages: fil })

  it("names the number when it's more than one", () => {
    expect(t("start.freeCandidates", { count: 3 })).toContain("3")
    expect(t("pricing.welcome", { count: 3 })).toContain("3")
    expect(t("landing.freeToStart.free", { count: 3 })).toContain("3")
  })

  it("says the first one when it's one", () => {
    expect(t("pricing.welcome", { count: 1 })).toBe("Ang iyong unang aplikante")
  })
})
