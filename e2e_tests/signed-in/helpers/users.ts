import { randomBytes } from "node:crypto"
import { hostname } from "node:os"

/** This run's tag in every throwaway address: its container's id (the host name Docker gives it,
 * the same in the tests and in teardown.ts), so a run's clean-up deletes only its own accounts
 * and runs at the same time don't sign each other's users out. */
export const RUN = hostname().replace(/[^0-9a-f]/g, "").slice(0, 12) || "local"

/** A short random part, so each run's users, companies and domains are new. */
export function randomId() {
  return randomBytes(4).toString("hex")
}

/** A throwaway address for someone the tests invite. Invites are emailed, and locally they may go
 * through Resend: its test domain takes any +label and delivers to nobody (like e2e.py). */
export function throwawayEmail(label: string) {
  return `delivered+e2e-${label}-${RUN}-${randomId()}@resend.dev`
}

/** A throwaway address for a company owner, on a reserved domain that never receives mail. Each
 * is its own inbox: a first company's welcome credits come once per inbox, and the +labels of
 * throwawayEmail all share one. */
export function ownerEmail(domain = "example.com") {
  return `e2e-owner-${RUN}-${randomId()}@${domain}`
}
