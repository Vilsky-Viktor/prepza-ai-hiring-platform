import type { Locator } from "@playwright/test"

import { expect, test } from "../fixtures"
import { createCompany } from "../helpers/api"
import { box } from "../helpers/layout"
import { integrationRow, visit } from "../helpers/navigation"
import { throwawayEmail } from "../helpers/users"

/** The titled group (a section with its heading) `row` is in. */
function groupOf(row: Locator) {
  return row.locator("xpath=ancestor::section[1]")
}

// The integrations tab has three groups, each under its own heading, one under another:
// messaging (Slack), then the API and AI apps together in one list, then the ATSs.
test("the integrations tab groups messaging, then the API and AI apps, then the ATSs", async ({
  signInAs,
}) => {
  test.setTimeout(180_000)
  const owner = await signInAs(throwawayEmail("integrations-order"))
  const company = await createCompany(owner)
  await visit(owner, `/companies/${company.id}/integrations`)

  const slack = integrationRow(owner, "/slack")
  const api = integrationRow(owner, "/api")
  const ai = integrationRow(owner, "/ai")
  const ats = integrationRow(owner, "/workable")

  for (const row of [slack, api, ai, ats]) {
    await expect(row).toBeVisible()
    await expect(groupOf(row).getByRole("heading", { level: 2 })).toHaveCount(1)
  }

  // The API and AI apps share one list; Slack and the ATSs each have a group of their own.
  await expect(groupOf(api).getByRole("list")).toHaveCount(1)
  await expect(groupOf(api).getByRole("list").filter({ has: ai })).toHaveCount(1)
  await expect(groupOf(slack).filter({ has: api })).toHaveCount(0)
  await expect(groupOf(ats).filter({ has: api })).toHaveCount(0)

  // In that order down the page.
  const [messaging, apiAndAi, atss] = await Promise.all(
    [slack, api, ats].map((row) => box(groupOf(row))),
  )
  expect(apiAndAi.top).toBeGreaterThanOrEqual(messaging.bottom)
  expect(atss.top).toBeGreaterThanOrEqual(apiAndAi.bottom)
  expect((await box(ai)).top).toBeGreaterThan((await box(api)).top)

  // On a computer each row's grey logo tile is as tall as its row, however tall the row is.
  for (const row of [slack, api, ai, ats]) {
    const logo = await box(row.getByRole("link").locator("> span").first())
    const whole = await box(row)
    expect(Math.abs(logo.height - whole.height)).toBeLessThanOrEqual(1)
    expect(Math.abs(logo.top - whole.top)).toBeLessThanOrEqual(1)
  }
})
