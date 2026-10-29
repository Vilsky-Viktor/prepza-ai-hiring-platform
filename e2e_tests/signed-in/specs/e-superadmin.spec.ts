import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { api, createCompany } from "../helpers/api"
import { addReplacedVersion, addTemplate, deleteTemplate } from "../helpers/db-library"
import { openDialog, visit, visitUntil } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { ownerEmail, randomId } from "../helpers/users"

// The controls page's switches, in their order on the page.
const PAUSE = 0
const MAINTENANCE = 1

/** A switch on the admin zone's controls page, by its place on it. */
function control(page: Page, index: number) {
  return page.getByRole("main").getByRole("switch").nth(index)
}

test("superadmin sorts pass rates", async ({ signInSuperadmin }) => {
  const superadmin = await signInSuperadmin()
  await visit(superadmin, "/superadmin/pass-rates")
  // The sort: a gray pill above the list, opening the orders; lowest pass rate first, then most
  // finished first.
  const sort = superadmin.getByRole("main").getByRole("button").first()
  const orders = superadmin.getByRole("menu").getByRole("menuitemradio")
  await shot(superadmin, "pass-rates")

  async function openSort() {
    await expect(async () => {
      await sort.click()
      await expect(superadmin.getByRole("menu")).toBeVisible({ timeout: 2_000 })
    }).toPass()
  }

  await openSort()
  await expect(orders.first()).toHaveAttribute("aria-checked", "true")
  await shot(superadmin, "pass-rates-sort-menu")
  await orders.nth(1).click()
  await expect(superadmin).toHaveURL(/sort=finished/)
  await shot(superadmin, "pass-rates-by-finished")
  await openSort()
  await expect(orders.nth(1)).toHaveAttribute("aria-checked", "true")
})

test("superadmin sees a month's stats, a year's and all time, kept after a reload", async ({
  signInSuperadmin,
}) => {
  const superadmin = await signInSuperadmin()
  await visit(superadmin, "/superadmin/stats/general")
  // A fresh start: this month.
  await superadmin.evaluate(() => localStorage.removeItem("prepza_stats_period"))
  await visit(superadmin, "/superadmin/stats/general")
  const now = new Date()
  const thisMonth = now.toLocaleString("en-US", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  })
  const thisYear = String(now.getUTCFullYear())
  // The period's pill, the page's one button, and the all-time box beside it.
  const period = superadmin.getByRole("main").getByRole("button").first()
  const allTime = superadmin.getByRole("checkbox")
  await expect(period).toHaveText(thisMonth)
  const cards = superadmin.locator("dl")
  await expect(cards.getByRole("term")).toHaveCount(10)
  // Every service answered: no card is left as a dash.
  await expect(cards.getByRole("definition").filter({ hasText: /^—$/ })).toHaveCount(0)
  await shot(superadmin, "stats")
  // One choice in the menu: a month with its year, or a year.
  await period.click()
  await expect(superadmin.getByRole("menuitemradio", { name: thisMonth })).toHaveAttribute(
    "aria-checked",
    "true"
  )
  await shot(superadmin, "stats-menu")
  await superadmin.getByRole("menuitemradio", { name: thisYear, exact: true }).click()
  await expect(period).toHaveText(thisYear)
  // All time turns the menu off, keeping its year.
  await allTime.click()
  await expect(allTime).toBeChecked()
  await expect(period).toBeDisabled()
  await shot(superadmin, "stats-all-time")
  // The browser keeps the choice; the address doesn't change.
  await expect(superadmin).toHaveURL(/\/superadmin\/stats\/general$/)
  await superadmin.reload()
  await expect(allTime).toBeChecked()
  await expect(period).toHaveText(thisYear)
  await allTime.click()
  await expect(period).toBeEnabled()
})

/** Turns a switch on the controls page, opened afresh: the dev frontend may have reloaded it. */
async function flip(page: Page, index: number, on: boolean) {
  await visit(page, "/superadmin/controls")
  const toggle = control(page, index)
  await expect(toggle).toBeChecked({ checked: !on })
  await toggle.click()
  await expect(toggle).toBeChecked({ checked: on })
}

async function paused(page: Page) {
  return (await api<{ paused: boolean }>(page, "GET", "/companies/pause")).paused
}

async function maintenanceOn(page: Page) {
  return (await api<{ on: boolean }>(page, "GET", "/companies/superadmin/maintenance")).on
}

// Both switches are global: they're turned on only when found off, and always turned off again
// when the test ends, even when a step fails or it runs out of time (switchesOffAfter). Tagged
// @global: it runs alone, after the other tests (signed-in.sh).
test("superadmin turns the pause and maintenance mode on and off", { tag: "@global" }, async ({
  signInAs,
  signInSuperadmin,
  switchesOffAfter,
}) => {
  const owner = await signInAs(ownerEmail())
  const company = await createCompany(owner)
  const superadmin = await signInSuperadmin()
  test.skip(
    (await paused(superadmin)) || (await maintenanceOn(superadmin)),
    "The pause or maintenance mode is already on: left as it is"
  )
  await switchesOffAfter(superadmin)

  await visit(superadmin, "/superadmin/controls")
  await shot(superadmin, "controls")
  await flip(superadmin, PAUSE, true)
  await expect.poll(() => paused(superadmin)).toBe(true)
  await shot(superadmin, "pause-on")

  const newInterview = `/companies/${company.id}/interviews/new`
  const description = owner.getByRole("main").getByRole("textbox")
  await visit(owner, newInterview)
  await expect(owner.getByTestId("paused-notice").filter({ visible: true })).toBeVisible()
  // The start box is there but off, so it's clearly unavailable.
  await expect(description).toBeDisabled()
  await shot(owner, "new-interview-paused")
  // A job ad's link says so too, as an invite does: no new candidate can start.
  await visit(owner, "/apply/e2e-paused-link")
  await expect(owner.getByTestId("paused-notice").filter({ visible: true })).toBeVisible()
  await shot(owner, "job-link-paused")
  await flip(superadmin, PAUSE, false)
  await expect.poll(() => paused(superadmin)).toBe(false)
  await visit(owner, newInterview)
  await expect(description).toBeEnabled()
  await expect(owner.getByTestId("paused-notice")).toHaveCount(0)

  // Maintenance asks first.
  await visit(superadmin, "/superadmin/controls")
  await control(superadmin, MAINTENANCE).click()
  const dialog = superadmin.getByRole("dialog")
  await expect(dialog).toBeVisible()
  // Not on until confirmed.
  expect(await maintenanceOn(superadmin)).toBe(false)
  await shot(superadmin, "maintenance-confirm")
  await dialog.getByRole("button").last().click()
  await expect(dialog).toBeHidden()
  await expect.poll(() => maintenanceOn(superadmin)).toBe(true)

  // Everyone else gets the maintenance screen; superadmins the site, with a warning card.
  await visitUntil(owner, "/companies", 503)
  await expect(owner.getByText(company.name)).toHaveCount(0)
  await shot(owner, "maintenance-screen")
  // The legal texts stay readable.
  await visitUntil(owner, "/privacy", 200)
  await expect(owner.getByRole("heading", { level: 1 })).toBeVisible()
  await shot(owner, "maintenance-privacy")
  // Superadmins keep the site, with the warning card above it.
  await expect(async () => {
    await visit(superadmin, "/companies")
    await expect(superadmin.getByTestId("maintenance-notice").filter({ visible: true })).toBeVisible({
      timeout: 2_000,
    })
  }).toPass({ timeout: 60_000 })
  await shot(superadmin, "maintenance-superadmin")

  await flip(superadmin, MAINTENANCE, false)
  await expect.poll(() => maintenanceOn(superadmin)).toBe(false)
  await visitUntil(owner, "/companies", 200)
  // The visible card: while the page renders again, Next.js can keep a hidden copy of it.
  await expect(owner.getByText(company.name).filter({ visible: true })).toBeVisible()
})

// A replaced question shows, behind its "replaced with" button, the question that took its place.
test("superadmin sees what a replaced question was replaced with", async ({ signInSuperadmin }) => {
  const oldText = `E2E old question ${randomId()}?`
  const templateId = await addTemplate(`E2E replaced ${randomId()}`, 1)
  await addReplacedVersion(templateId, oldText)

  try {
    const superadmin = await signInSuperadmin()
    await visit(superadmin, "/superadmin/questions/replaced")
    const row = superadmin.getByRole("listitem").filter({ hasText: oldText })
    await expect(row).toBeVisible()
    await shot(superadmin, "replaced")
    await row.getByTestId("replaced-with").click()
    const dialog = superadmin.getByRole("dialog")
    await expect(dialog).toContainText("E2E question 1?")
    await expect(dialog).toContainText("Skip the check")
    await shot(superadmin, "replaced-with")
  } finally {
    await deleteTemplate(templateId)
  }
})

test("superadmin sees each legal document's notice on the controls page", async ({
  signInSuperadmin,
}) => {
  const superadmin = await signInSuperadmin()
  await visit(superadmin, "/superadmin/controls")
  // The notices' list: the terms, the privacy policy and the data processing agreement.
  await expect(superadmin.getByTestId("legal-notices").getByRole("listitem")).toHaveCount(3)
  await shot(superadmin, "legal-notices")
})

// A template's page shows each topic's practice and company questions. One short of either can
// be topped up; any can get more questions, by default the backend's number (nothing is started
// here: that would write questions with OpenAI).
test("superadmin sees a template's practice and company questions per topic", async ({
  signInSuperadmin,
}) => {
  const templateId = await addTemplate(`E2E pools ${randomId()}`, 12)

  try {
    const superadmin = await signInSuperadmin()
    await visit(superadmin, `/superadmin/templates/${templateId}`)
    // Practice first, then company.
    await expect(superadmin.getByTestId("pool-counts")).toHaveText(/^0\D+12\D*$/)
    await expect(superadmin.getByTestId("top-up").filter({ visible: true })).toBeVisible()
    await shot(superadmin, "template-pools")
    await openDialog(superadmin, superadmin.getByTestId("add-questions"))
    await expect(superadmin.getByRole("dialog").getByRole("spinbutton")).toHaveValue("30")
    await shot(superadmin, "add-questions")
    await superadmin.keyboard.press("Escape")
  } finally {
    await deleteTemplate(templateId)
  }
})
