// The admin zone's stats tab: each card in order, the service whose stats it comes from (its
// API path) and the metric there. Paid comes apart, in cents per currency.
export const STATS_CARDS = [
  { source: "library", metric: "users" },
  { source: "companies", metric: "companies" },
  { source: "companies", metric: "verified" },
  { source: "companies", metric: "interviews" },
  { source: "companies", metric: "invited" },
  { source: "companies", metric: "finished" },
  { source: "rounds", metric: "practice" },
  { source: "billing", metric: "top_ups" },
  { source: "billing", metric: "paid" },
  { source: "billing", metric: "credits_spent" },
] as const

export const STATS_SOURCES = [
  "library",
  "companies",
  "rounds",
  "billing",
] as const

// The year prepza launched: the first year the menu offers.
export const STATS_FIRST_YEAR = 2026

// Where the browser keeps the superadmin's last choice (all time, and the year or month).
export const STATS_STORAGE_KEY = "prepza_stats_period"
