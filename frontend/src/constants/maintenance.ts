// Maintenance mode, as proxy.ts finds it for each page request: "closed" shows the maintenance
// screen, "open" lets a superadmin through with a notice, "off" is the usual site.
export const MAINTENANCE_HEADER = "x-maintenance"
// How long the answer for everyone is kept; only while it's on is the signed-in user asked about.
export const MAINTENANCE_CACHE_MS = 10_000
// The check must never hold up or take down the site: no answer in time means off.
export const MAINTENANCE_TIMEOUT_MS = 2_000
// Pages shown as usual even then: unsubscribing must always work, and the legal texts stay
// readable (their services leave the same open).
export const MAINTENANCE_OPEN_PAGES = [
  "/unsubscribe",
  "/privacy",
  "/terms",
  "/dpa",
  "/documents",
  "/accessibility",
]
