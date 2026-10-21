import type { Catalog } from "@/types/billing"

/** A moment as a medium date in the language asked, in `timeZone` (the runtime's when none).
 * Pages show moments through useLocalTime or LocalDate, in the visitor's own time zone. */
export function formatDate(iso: string, locale: string, timeZone?: string) {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeZone,
  }).format(new Date(iso))
}

/** A moment as a medium date and a short time in the language asked, in `timeZone` (the
 * runtime's when none), like formatDate. */
export function formatDateTime(iso: string, locale: string, timeZone?: string) {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone,
  }).format(new Date(iso))
}

/** A calendar day ("2026-10-08") as a medium date in the language asked: the same day in every
 * time zone. */
export function formatDay(day: string, locale: string) {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(new Date(day))
}

/** The browser's day today, as a date field takes it ("2026-10-08"). */
export function today(now = new Date()) {
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")

  return `${now.getFullYear()}-${month}-${day}`
}

/** The moment a day a date field gave ("2026-10-08") starts in the browser's time zone, as the
 * API takes it; `after` days later (1: the moment it ends). */
export function dayStart(day: string, after = 0) {
  const [year, month, date] = day.split("-").map(Number)

  return new Date(year, month - 1, date + after).toISOString()
}

/** An amount in a currency's smallest unit, as billing and Paddle count it (cents; yen and won
 * themselves), in the currency's whole units: 2400 cents are 24 dollars, 750 yen are 750 yen. */
export function moneyAmount(minor: number, currency: string) {
  const digits =
    new Intl.NumberFormat("en", {
      style: "currency",
      currency,
    }).resolvedOptions().maximumFractionDigits ?? 2

  return minor / 10 ** digits
}

/** 2400 cents in USD: "$24"; a whole amount without decimals, others with the currency's. */
export function formatPrice(cents: number, currency: string, locale: string) {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    trailingZeroDisplay: "stripIfInteger",
  }).format(moneyAmount(cents, currency))
}

/** 100 to 300 cents in USD: "$1–$3", written as the locale writes a range; a whole amount
 * without decimals, as formatPrice ("£1.50–£4"). */
export function formatPriceRange(
  minCents: number,
  maxCents: number,
  currency: string,
  locale: string
) {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    trailingZeroDisplay: "stripIfInteger",
  }).formatRange(
    moneyAmount(minCents, currency),
    moneyAmount(maxCents, currency)
  )
}

/** What a candidate costs in the catalog, cheapest to standard, as the locale writes a range
 * ("$2–5"); empty without the catalog, which the messages then leave out. */
export function candidatePriceRange(catalog: Catalog | null, locale: string) {
  if (!catalog) {
    return ""
  }

  return formatPriceRange(
    catalog.candidate_cents_min,
    catalog.candidate_cents_max,
    catalog.currency,
    locale
  )
}

/** A count as the locale writes it short: 950, "1.5K", "250K", "1.2M". */
export function compactNumber(value: number, locale: string) {
  return new Intl.NumberFormat(locale, {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value)
}

/** Money short from 1,000 of the currency up ("$12.3K", "¥1.5M"); exact below it ("$66.60"). */
export function compactPrice(cents: number, currency: string, locale: string) {
  const amount = moneyAmount(cents, currency)

  if (amount < 1_000) {
    return formatPrice(cents, currency, locale)
  }

  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(amount)
}

/** US dollars as AI costs come (not cents): to the cent from $1 up, and to three significant
 * digits below it, so one call's cost ("$0.00123") still shows. */
export function formatUsd(value: number, locale: string) {
  const small = value > 0 && value < 1

  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "USD",
    ...(small
      ? { maximumSignificantDigits: 3 }
      : { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
  }).format(value)
}

/** Seconds as the language writes them short ("75 sec", "75 s"). */
export function formatSeconds(value: number, locale: string) {
  return new Intl.NumberFormat(locale, {
    style: "unit",
    unit: "second",
    unitDisplay: "short",
  }).format(value)
}

/** A percentage (0 to 100) as the language writes it ("85 %" in French, "%85" in Turkish); "—"
 * for none (a grade not known yet). */
export function formatPercent(
  value: number | null | undefined,
  locale: string
) {
  return value == null
    ? "—"
    : new Intl.NumberFormat(locale, { style: "percent" }).format(value / 100)
}
