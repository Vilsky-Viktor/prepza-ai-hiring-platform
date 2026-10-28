import { STATS_FIRST_YEAR, STATS_STORAGE_KEY } from "@/constants/stats"

/** What the stats tab shows: all time, or a year ("2026") or month ("2026-07") in UTC. */
export type StatsChoice = { allTime: boolean; period: string }

const PERIOD = /^\d{4}(-(0[1-9]|1[0-2]))?$/

/** The years the menu offers, newest first: every year since launch. */
export function statsYears(now: Date) {
  const year = now.getUTCFullYear()

  return Array.from(
    { length: Math.max(1, year - STATS_FIRST_YEAR + 1) },
    (_, index) => String(year - index)
  )
}

/** The months the menu offers, newest first: the last 12, none before launch ("2026-10"). */
export function statsMonths(now: Date) {
  return Array.from({ length: 12 }, (_, index) =>
    new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - index, 15))
      .toISOString()
      .slice(0, 7)
  ).filter((month) => Number(month.slice(0, 4)) >= STATS_FIRST_YEAR)
}

/** The saved choice as stored, "" when there's none or storage is blocked (a private window). */
export function savedStatsChoice() {
  try {
    return localStorage.getItem(STATS_STORAGE_KEY) ?? ""
  } catch {
    return ""
  }
}

/** The choice to start with: the saved one when it still reads right, else this month. */
export function parseStatsChoice(saved: string, now: Date): StatsChoice {
  const fallback = { allTime: false, period: now.toISOString().slice(0, 7) }

  try {
    const value = JSON.parse(saved || "null")

    return value &&
      typeof value.allTime === "boolean" &&
      typeof value.period === "string" &&
      PERIOD.test(value.period)
      ? { allTime: value.allTime, period: value.period }
      : fallback
  } catch {
    return fallback
  }
}

/** Keeps the choice for the next visit; nothing happens when storage is blocked. */
export function writeStatsChoice(choice: StatsChoice) {
  try {
    localStorage.setItem(STATS_STORAGE_KEY, JSON.stringify(choice))
  } catch {
    // The choice simply isn't remembered.
  }
}
