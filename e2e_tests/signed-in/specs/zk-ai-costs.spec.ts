import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany } from "../helpers/api"
import { addAiCalls, addLimitHits, billingNow, deleteAiRows, deleteLimitChanges } from "../helpers/db-ai"
import { env } from "../helpers/env"
import { visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { uidOf } from "../helpers/sign-in"
import { ownerEmail, randomId } from "../helpers/users"

type Spend = { spend: number; calls: number; units?: number }
type Costs = {
  totals: Spend
  categories: (Spend & { category: string })[]
  actions: (Spend & { action: string; units: number })[]
}
type Limit = { name: string; value: number; default: number; highest: number; changed: boolean }

const DAY_MS = 24 * 60 * 60 * 1000
// A limit that records the test's hits: rarely hit, so its top companies and users are the test's.
const HIT_LIMIT = "MAX_WEBHOOKS"
// The limit the test changes: per user and minute for AI apps, so 59 for 60 disturbs nothing, and
// the MCP tools' public list says its value, read from the limits every service reads.
const EDITED_LIMIT = "MCP_CALLS_PER_USER_MINUTE"

/** Dollars as the page writes them (formatUsd): three significant digits under a dollar,
 * otherwise cents. */
function usd(value: number) {
  const small = value > 0 && value < 1

  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    ...(small
      ? { maximumSignificantDigits: 3 }
      : { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
  })
}

/** A row of the API's lists before the test added to it, or nothing yet. */
function before<T extends Spend>(rows: T[], key: keyof T, value: string): Spend {
  return rows.find((row) => row[key] === value) ?? { spend: 0, calls: 0, units: 0 }
}

/** A count as the page writes one, before its word ("2 calls"): not a part of another number or
 * an amount ("$2.60"). */
function counted(value: number) {
  return new RegExp(`(^|[^\\d.,$])${value}\\s`)
}

/** Picks a month in the period's menu, opening it again if the first click came too early. */
async function pickMonth(page: Page, label: string) {
  const period = page.getByRole("main").getByRole("button").first()

  await expect(async () => {
    await period.click()
    await expect(page.getByRole("menu")).toBeVisible({ timeout: 2_000 })
  }).toPass()
  await page.getByRole("menuitemradio", { name: label }).click()
  await expect(period).toHaveText(label)
}

// The test's calls and hits are in a month six months back, which the menu offers: the page
// shows them added to whatever that month already had, as the API had it before.
test("superadmin sees a month's AI costs, top spenders and limit hits", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const ownerAddress = ownerEmail()
  const owner = await signInAs(ownerAddress)
  const company = await createCompany(owner)
  const userId = await uidOf(owner)
  const now = new Date()
  const at = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() - 6, 15, 12))
  const period = at.toISOString().slice(0, 7)
  const label = at.toLocaleString("en-US", { month: "long", year: "numeric", timeZone: "UTC" })
  const superadmin = await signInSuperadmin()
  const was = await api<Costs>(superadmin, "GET", `/billing/superadmin/ai-costs?period=${period}`)
  const hitsWere = await api<{ ours: { limit: string; hits: number }[] }>(
    superadmin,
    "GET",
    `/billing/superadmin/limit-hits?period=${period}`
  )

  try {
    // Two interviews generated for the company; a conversation of its owner without a company.
    await addAiCalls([
      { action: "interview_generation", category: "paid", cost: 1.2, at, companyId: company.id, subjectId: `e2e-${randomId()}` },
      { action: "interview_generation", category: "paid", cost: 1.4, at, companyId: company.id, subjectId: `e2e-${randomId()}` },
      { action: "assistant_message", category: "no_company", cost: 1.5, at, userId, subjectId: `e2e-${randomId()}` },
    ])
    await addLimitHits(HIT_LIMIT, 2, at, company.id, userId)
    await visit(superadmin, "/superadmin/stats/ai-costs")
    await pickMonth(superadmin, label)

    // The totals.
    await expect(superadmin.getByTestId("number-spend").getByRole("definition")).toHaveText(
      usd(was.totals.spend + 4.1)
    )
    await expect(superadmin.getByTestId("number-calls").getByRole("definition")).toHaveText(
      String(was.totals.calls + 3)
    )
    // The paid companies' spend.
    const paid = before(was.categories, "category", "paid")
    await expect(superadmin.getByTestId("amount-paid")).toContainText(usd(paid.spend + 2.6))
    // Interview generation: its spend, what an interview cost, its calls, its paid share.
    const generation = before(was.actions, "action", "interview_generation")
    const generationSpend = generation.spend + 2.6
    const action = superadmin.getByTestId("amount-interview_generation")
    await expect(action).toContainText(usd(generationSpend))
    await expect(action).toContainText(usd(generationSpend / ((generation.units ?? 0) + 2)))
    await expect(action.getByTestId("amount-details")).toHaveText(counted(generation.calls + 2))
    await shot(superadmin, "ai-costs")

    // The company and the user among those that cost most, each opening its support page.
    const companyRow = superadmin.getByTestId(`amount-${company.id}`)
    await expect(companyRow).toContainText(company.name)
    await expect(companyRow).toContainText(usd(2.6))
    await expect(companyRow.getByTestId("amount-details")).toHaveText(counted(2))
    const userRow = superadmin.getByTestId(`amount-${userId}`)
    await expect(userRow).toContainText(ownerAddress)
    await expect(userRow).toContainText(usd(1.5))
    await expect(userRow.getByRole("link")).toHaveAttribute("href", `/superadmin/support/users/${userId}`)

    // The limit they hit, with its hits, and them as its hitters, each opening its support page.
    const hitsBefore = hitsWere.ours.find((row) => row.limit === HIT_LIMIT)?.hits ?? 0
    const hit = superadmin.getByTestId(`amount-ours-${HIT_LIMIT}`)
    await expect(hit).toHaveText(counted(hitsBefore + 2))
    await expect(hit.locator(`a[href="/superadmin/support/companies/${company.id}"]`)).toHaveText(
      `${company.name} (2)`
    )
    await expect(hit.locator(`a[href="/superadmin/support/users/${userId}"]`)).toHaveText(
      `${ownerAddress} (2)`
    )
    await hit.scrollIntoViewIfNeeded()
    await shot(superadmin, "ai-costs-limit-hits")

    // A support page is a server render, slow on a cold dev server.
    await companyRow.getByRole("link").click()
    await expect(superadmin).toHaveURL(new RegExp(`/superadmin/support/companies/${company.id}$`), {
      timeout: 90_000,
    })
    await expect(superadmin.getByRole("heading", { level: 1 })).toHaveText(company.name)
  } finally {
    await deleteAiRows(company.id, userId)
  }
})

// A limit's change is global: the test changes one only when it's at its default, and always sets
// it back and removes its history entries, even when a step fails. Tagged @global: it runs alone,
// after the other tests (signed-in.sh).
test("superadmin changes a limit, the services apply it, and sets it back", { tag: "@global" }, async ({
  signInSuperadmin,
}) => {
  const superadmin = await signInSuperadmin()
  const limits = await api<{ limits: Limit[] }>(superadmin, "GET", "/billing/superadmin/limits")
  const limit = limits.limits.find((found) => found.name === EDITED_LIMIT)!
  test.skip(limit.changed, "The limit is already changed locally: left as it is")
  const email = env("SUPERADMIN_EMAILS").split(",")[0].trim().toLowerCase()
  const applied = async () =>
    (await api<{ limits: { calls_per_minute: number } }>(superadmin, "GET", "/assistant/mcp/tools"))
      .limits.calls_per_minute
  const start = await billingNow()
  const changed = limit.default - 1

  try {
    await visit(superadmin, "/superadmin/controls")
    const row = superadmin.getByTestId(`limit-${EDITED_LIMIT}`)
    const field = row.getByRole("spinbutton")
    const buttons = row.getByRole("button")
    // The change, its from and to; then who made it and when.
    const latest = superadmin.getByTestId("limit-changes").getByRole("listitem").first()
    const latestChange = latest.locator("span").first()
    await expect(field).toHaveValue(String(limit.default))
    // Only Save: nothing to set back.
    await expect(buttons).toHaveCount(1)

    // Out of its bounds, the field itself refuses it; past the browser's check, the API refuses
    // it, saying why.
    await field.fill(String(limit.highest + 1))
    await buttons.first().click()
    expect(await field.evaluate((input: HTMLInputElement) => input.validity.valid)).toBe(false)
    await row.locator("form").evaluate((form: HTMLFormElement) => (form.noValidate = true))
    await buttons.first().click()
    await expect(superadmin.locator('[data-sonner-toast][data-type="error"]')).toContainText(
      `Use a value from 1 to ${limit.highest}.`
    )
    expect((await api<{ limits: Limit[] }>(superadmin, "GET", "/billing/superadmin/limits")).limits
      .find((found) => found.name === EDITED_LIMIT)?.changed).toBe(false)

    await field.fill(String(changed))
    await buttons.first().click()
    await expect(superadmin.locator('[data-sonner-toast][data-type="success"]')).toBeVisible()
    await expect(field).toHaveValue(String(changed))
    await expect(buttons).toHaveCount(2)
    // From its default to the new value.
    await expect(latestChange).toHaveText(new RegExp(`\\D${changed}$`))
    await expect(latestChange).not.toHaveText(new RegExp(`\\b${limit.default}\\b`))
    await expect(latest).toContainText(email)
    await shot(superadmin, "limit-changed")
    // Every service reads it within half a minute (LIMITS_CACHE_SECONDS).
    await expect.poll(applied, { timeout: 60_000, intervals: [3_000] }).toBe(changed)
    await visit(superadmin, "/superadmin/controls")
    await expect(field).toHaveValue(String(changed))

    // Set back: the default again, and a second entry from the changed value.
    await buttons.last().click()
    await expect(field).toHaveValue(String(limit.default))
    await expect(buttons).toHaveCount(1)
    await expect(latestChange).toHaveText(new RegExp(`\\D${changed}\\D+$`))
    await expect(latestChange).not.toHaveText(new RegExp(`\\b${limit.default}\\b`))
    await expect(latest).toContainText(email)
    await expect(
      superadmin.getByTestId("limit-changes").getByRole("listitem").nth(1).locator("span").first()
    ).toHaveText(new RegExp(`\\D${changed}$`))
    await shot(superadmin, "limit-reset")
    await expect.poll(applied, { timeout: 60_000, intervals: [3_000] }).toBe(limit.default)
  } finally {
    const now = (await api<{ limits: Limit[] }>(superadmin, "GET", "/billing/superadmin/limits"))
      .limits.find((found) => found.name === EDITED_LIMIT)

    if (now?.changed) {
      await api(superadmin, "DELETE", `/billing/superadmin/limits/${EDITED_LIMIT}`)
    }

    await deleteLimitChanges(EDITED_LIMIT, start)
  }
})

// A company's and a user's support pages say what AI cost for them in the last 30 days: calls
// older than that don't count.
test("a support page shows its company's and user's AI cost of the last 30 days", async ({
  signInAs,
  signInSuperadmin,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const userId = await uidOf(owner)
  const daysAgo = (days: number) => new Date(Date.now() - days * DAY_MS)

  try {
    await addAiCalls([
      { action: "interview_generation", category: "paid", cost: 1.2, at: daysAgo(1), companyId: company.id },
      { action: "interview_generation", category: "paid", cost: 0.3, at: daysAgo(2), companyId: company.id },
      { action: "interview_generation", category: "paid", cost: 5, at: daysAgo(40), companyId: company.id },
      { action: "assistant_message", category: "no_company", cost: 2.25, at: daysAgo(3), userId },
      { action: "assistant_message", category: "no_company", cost: 4, at: daysAgo(45), userId },
    ])
    const superadmin = await signInSuperadmin()
    const line = superadmin.getByTestId("ai-spend")

    await visit(superadmin, `/superadmin/support/companies/${company.id}`)
    await expect(line).toContainText(usd(1.5))
    await expect(line).toHaveText(counted(2))
    await shot(superadmin, "support-company-ai-spend")
    await visit(superadmin, `/superadmin/support/users/${userId}`)
    await expect(line).toContainText(usd(2.25))
    await expect(line).toHaveText(counted(1))
    await shot(superadmin, "support-user-ai-spend")
  } finally {
    await deleteAiRows(company.id, userId)
  }
})
