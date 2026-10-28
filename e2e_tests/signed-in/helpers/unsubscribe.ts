import { expect, type Page } from "@playwright/test"
import { createHash, createHmac } from "node:crypto"

import { env } from "./env"

// An email's unsubscribe link, signed the way notifications signs it
// (services/notifications/src/notifications/helpers/unsubscribe.py) with the stack's
// EMAIL_LINK_SECRET. The signed-out page tests (e2e_tests/pages/unsubscribe.spec.ts) keep their
// own copy: each suite is its own package. The secret is read here and never printed.
function sign(payload: object): string {
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url")
  const signature = createHmac("sha256", env("EMAIL_LINK_SECRET"))
    .update(`unsubscribe:${body}`)
    .digest("base64url")

  return `${body}.${signature}`
}

/** The page a user's link opens: `kind` is what it stops, such as "digest". */
export function userUnsubscribePath(userId: string, kind: string): string {
  return `/unsubscribe?token=${sign({ type: kind, user_id: userId })}`
}

/** The page a candidate's "Don't email me for <company>" link opens. */
export function companyUnsubscribePath(email: string, companyId: string, company: string): string {
  const address = createHash("sha256").update(email.trim().toLowerCase()).digest("hex")

  return `/unsubscribe?token=${sign({ type: "company", address, company_id: companyId, company })}`
}

/** Confirms an unsubscribe link's page (its one button) and waits for the API to take it. */
export async function confirmUnsubscribe(page: Page) {
  const saved = page.waitForResponse(
    (response) =>
      response.url().includes("/notifications/unsubscribe/") &&
      response.request().method() === "POST"
  )
  await page.getByRole("main").getByRole("button").click()
  expect((await saved).ok()).toBe(true)
}
