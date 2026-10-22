import { describe, expect, it } from "vitest"
import type { Catalog } from "@/types/billing"

import {
  dayStart,
  formatDate,
  formatDateTime,
  formatDay,
  formatList,
  formatPercent,
  formatPrice,
  candidatePriceRange,
  formatPriceRange,
  moneyAmount,
  formatSeconds,
  formatUsd,
  today,
} from "@/lib/format"

// Intl puts no-break spaces in some languages' numbers and currencies.
function plain(text: string) {
  return text.replace(/[  ]/g, " ")
}

describe("formatDate", () => {
  // Midday UTC: the same day in every time zone the tests may run in.
  const iso = "2026-03-05T12:00:00Z"

  it("writes a medium date in the language asked", () => {
    expect(formatDate(iso, "en")).toBe("Mar 5, 2026")
    expect(formatDate(iso, "de")).toBe("05.03.2026")
  })

  it("writes the day in the time zone asked", () => {
    // 2:00 UTC is still the evening before in New York.
    const late = "2026-10-15T02:00:00Z"

    expect(formatDate(late, "en", "UTC")).toBe("Oct 15, 2026")
    expect(formatDate(late, "en", "America/New_York")).toBe("Oct 14, 2026")
    expect(formatDateTime(late, "en", "America/New_York")).toBe(
      "Oct 14, 2026, 10:00 PM"
    )
  })
})

describe("formatDay", () => {
  it("writes the day itself, whatever the time zone", () => {
    expect(formatDay("2026-03-05", "en")).toBe("Mar 5, 2026")
    expect(formatDay("2026-03-05", "de")).toBe("05.03.2026")
  })
})

describe("today", () => {
  it("is the local day as a date field takes it", () => {
    expect(today(new Date(2026, 0, 9, 23, 30))).toBe("2026-01-09")
    expect(today(new Date(2026, 11, 31, 0, 5))).toBe("2026-12-31")
  })
})

describe("dayStart", () => {
  it("is when a local day starts, or ends with one day after", () => {
    expect(dayStart("2026-10-08")).toBe(new Date(2026, 9, 8).toISOString())
    expect(dayStart("2026-10-31", 1)).toBe(new Date(2026, 10, 1).toISOString())
  })

  it("gives back the same day in a date field, as the action log's filter shows it", () => {
    const end = new Date(dayStart("2026-12-31", 1)).getTime()

    expect(today(new Date(dayStart("2026-12-31")))).toBe("2026-12-31")
    expect(today(new Date(end - 1))).toBe("2026-12-31")
  })
})

describe("formatPrice", () => {
  it("leaves out the cents of a whole amount", () => {
    expect(formatPrice(2400, "USD", "en")).toBe("$24")
    expect(formatPrice(100000, "USD", "en")).toBe("$1,000")
  })

  it("shows the cents of an amount that has them", () => {
    expect(formatPrice(2450, "USD", "en")).toBe("$24.50")
    expect(formatPrice(99, "USD", "en")).toBe("$0.99")
  })

  it("follows the language's way of writing money", () => {
    expect(plain(formatPrice(2450, "EUR", "de"))).toBe("24,50 €")
    expect(plain(formatPrice(2400, "EUR", "de"))).toBe("24 €")
  })
})

describe("formatPriceRange", () => {
  it("writes a price range as the language does", () => {
    expect(plain(formatPriceRange(100, 300, "USD", "en"))).toBe("$1 – $3")
    expect(plain(formatPriceRange(100, 300, "USD", "de"))).toBe("1–3 $")
  })

  it("shows cents only where an end has them, as each currency writes them", () => {
    expect(plain(formatPriceRange(50, 300, "USD", "en"))).toBe("$0.50 – $3")
    expect(plain(formatPriceRange(150, 400, "GBP", "en"))).toBe("£1.50 – £4")
    expect(plain(formatPriceRange(200, 500, "EUR", "fr"))).toBe("2–5 €")
  })
})

describe("moneyAmount", () => {
  it("reads billing's amounts in each currency's smallest unit, whole yen and won", () => {
    expect(moneyAmount(2400, "USD")).toBe(24)
    expect(moneyAmount(750, "JPY")).toBe(750)
    expect(moneyAmount(7000, "KRW")).toBe(7000)
    expect(plain(formatPrice(750, "JPY", "en"))).toBe("¥750")
    expect(plain(formatPriceRange(300, 750, "JPY", "en"))).toBe("¥300 – ¥750")
  })

  // Paddle's decimal places for every currency billing sells in (its API's GET /currencies,
  // 2026-10-21): the site must read billing's minor units the way Paddle counts them.
  it.each([
    ["USD", 2],
    ["EUR", 2],
    ["GBP", 2],
    ["CAD", 2],
    ["AUD", 2],
    ["ILS", 2],
    ["PLN", 2],
    ["JPY", 0],
    ["KRW", 0],
    ["TWD", 2],
    ["HKD", 2],
    ["CHF", 2],
    ["THB", 2],
    ["SGD", 2],
    ["INR", 2],
  ])("reads %s with Paddle's %i decimal places", (currency, decimals) => {
    expect(moneyAmount(12345, currency as string)).toBe(
      12345 / 10 ** (decimals as number)
    )
  })
})

describe("candidatePriceRange", () => {
  it("is the catalog's cheapest to standard price in its currency, or empty without one", () => {
    const catalog = {
      currency: "GBP",
      candidate_cents_min: 150,
      candidate_cents_max: 400,
    } as Catalog

    expect(plain(candidatePriceRange(catalog, "en"))).toBe("£1.50 – £4")
    expect(candidatePriceRange(null, "en")).toBe("")
  })
})

describe("formatPercent", () => {
  it("writes a percentage as each language does, and a dash for none", () => {
    expect(formatPercent(85, "en")).toBe("85%")
    expect(formatPercent(85, "tr")).toBe("%85")
    expect(formatPercent(85, "fr")).toMatch(/^85\s%$/)
    expect(formatPercent(85, "de")).toMatch(/^85\s%$/)
    expect(formatPercent(null, "en")).toBe("—")
  })

  it("writes a plus before an added share when asked", () => {
    expect(formatPercent(25, "en", true)).toBe("+25%")
    expect(formatPercent(25, "tr", true)).toBe("+%25")
    expect(formatPercent(0, "en", true)).toBe("0%")
  })
})

describe("formatList", () => {
  it("lists items as each language does", () => {
    expect(formatList(["English", "French"], "en")).toBe("English, French")
    expect(formatList(["英語", "フランス語"], "ja")).toBe("英語、フランス語")
  })
})

describe("formatSeconds", () => {
  it("writes seconds short, as each language does", () => {
    expect(plain(formatSeconds(75, "en"))).toBe("75 sec")
    expect(plain(formatSeconds(75, "de"))).toBe("75 Sek.")
    expect(plain(formatSeconds(60, "ru"))).toBe("60 с")
  })
})

describe("formatUsd", () => {
  it("shows dollars to the cent from one dollar up", () => {
    expect(formatUsd(1234.5, "en")).toBe("$1,234.50")
    expect(formatUsd(0, "en")).toBe("$0.00")
  })

  it("keeps three significant digits below a dollar, so one call's cost shows", () => {
    expect(formatUsd(0.001234, "en")).toBe("$0.00123")
    expect(formatUsd(0.5, "en")).toBe("$0.5")
  })

  it("follows the language's way of writing money", () => {
    expect(plain(formatUsd(12.5, "de"))).toBe("12,50 $")
  })
})
