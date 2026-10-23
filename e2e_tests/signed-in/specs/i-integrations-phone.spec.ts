import type { Locator, Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { createCompany, createInterview } from "../helpers/api"
import { addAtsConnection, addSlackConnection, markAtsBroken } from "../helpers/db-integrations"
import { box, PHONE, settled } from "../helpers/layout"
import { integrationRow, openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

/** The page's content width: the header's (the page's visible width, without the scrollbar
 * desktop Chrome draws) inside its 24px side padding. */
async function contentWidth(page: Page) {
  return (await box(page.getByRole("banner"))).width - 48
}

/** What is drawn as the site's buttons in `scope`: buttons, and links drawn as buttons (the
 * docs), which are links to assistive tech. */
function drawnButtons(scope: Locator) {
  return scope.locator('button, a[data-slot="button"]')
}

/** The page's buttons (its integration's actions) sit on their own line under its title,
 * together as wide as the page. */
async function expectButtonsUnderTitle(page: Page) {
  const title = await box(page.getByRole("heading", { level: 1 }))
  const buttons = drawnButtons(page.getByRole("main").getByTestId("integration-actions"))
  await expect(buttons.first()).toBeVisible()
  const found = await Promise.all((await buttons.all()).map((button) => box(button)))

  for (const button of found) {
    expect(button.top).toBeGreaterThan(title.bottom)
  }

  const left = Math.min(...found.map((button) => button.left))
  const right = Math.max(...found.map((button) => button.right))
  expect(right - left).toBeGreaterThanOrEqual((await contentWidth(page)) - 2)
}

/** Reconnect (the third button: Instructions, Disconnect, Reconnect) takes a line of its own
 * under the other buttons, as wide as all of them. */
async function expectReconnectOwnLine(scope: Locator) {
  const actions = scope.getByTestId("integration-actions")
  const buttons = actions.getByRole("button")
  await expect(buttons).toHaveCount(3)
  const own = await box(buttons.nth(2))
  expect(Math.abs(own.width - (await box(actions)).width)).toBeLessThanOrEqual(2)
  expect(own.top).toBeGreaterThan((await box(buttons.nth(1))).bottom)
}

/** The Instructions dialog `button` opens fills the screen's height. */
async function expectFullHeightDialog(page: Page, button: Locator) {
  await openDialog(page, button)
  await settled(page.getByRole("dialog"))
  const dialog = await box(page.getByRole("dialog"))
  expect(Math.abs(dialog.height - PHONE.height)).toBeLessThanOrEqual(2)
  await page.keyboard.press("Escape")
  await expect(page.getByRole("dialog")).toHaveCount(0)
}

// On a phone the integrations tab's rows have a small logo beside the name and their buttons on
// the line under it; on Slack's, an ATS's and the API's pages the buttons go under the title,
// across the page, and the Instructions fill the screen. A connection that stopped working puts
// Reconnect on a line of its own.
test("the integrations pages on a phone", async ({ signInAs }) => {
  test.setTimeout(300_000)
  const owner = await signInAs(throwawayEmail("integrations-phone"))
  const company = await createCompany(owner)
  const interviewId = await createInterview(owner, company.id)
  const tab = `/companies/${company.id}/integrations`
  await addSlackConnection(company.id)
  await addAtsConnection(company.id, interviewId, { invited: 3, notInvited: 2 })
  // On a computer: each row's logo the row's full height, its buttons at the end of the line.
  await visit(owner, tab)
  await shot(owner, "tab-desktop")
  await owner.setViewportSize(PHONE)

  await visit(owner, tab)

  for (const path of ["/slack", "/workable", "/api", "/ai"]) {
    const row = integrationRow(owner, path)
    // The link's two parts: the logo, then the name and its text.
    const logo = await box(row.getByRole("link").locator("> span").first())
    const title = await box(row.getByRole("link").locator("> span").nth(1))
    const instructions = await box(drawnButtons(row).first())
    expect(logo.width, path).toBe(48)
    expect(logo.height, path).toBe(48)
    expect(title.left, path).toBeGreaterThan(logo.right)
    expect(instructions.top, path).toBeGreaterThan(Math.max(logo.bottom, title.bottom))
  }

  await shot(owner, "tab")
  await expectFullHeightDialog(owner, integrationRow(owner, "/workable").getByTestId("instructions"))

  // Slack: the buttons under the title; the notifications' box keeps its rounded corners.
  await visit(owner, `${tab}/slack`)
  await expectButtonsUnderTitle(owner)
  const kinds = owner
    .locator("main div.divide-y.rounded-xl")
    .filter({ has: owner.getByRole("checkbox") })
  await expect(kinds).not.toHaveCSS("border-top-left-radius", "0px")
  await shot(owner, "slack")

  // Workable: the buttons under the title, "Link a job" across the page under its text, and a
  // linked job's numbers on the line under its name.
  await visit(owner, `${tab}/workable`)
  await expectButtonsUnderTitle(owner)
  const linkJob = owner.getByTestId("link-job")
  const link = await box(linkJob)
  // Under the linked jobs' title and text, beside which it sits on a computer.
  const linksText = await box(linkJob.locator("xpath=preceding-sibling::div[1]"))
  expect(link.top).toBeGreaterThan(linksText.bottom)
  expect(link.width).toBeGreaterThanOrEqual((await contentWidth(owner)) - 2)
  const row = owner.getByRole("main").getByRole("listitem").filter({ hasText: "E2E Backend developer" })
  const job = await box(row.getByText("E2E Backend developer"))
  const invited = await box(row.getByTestId("invited-count"))
  // Unlink: the row's last button.
  const unlink = await box(row.getByRole("button").last())
  expect(invited.top).toBeGreaterThan(job.bottom)
  expect(unlink.top).toBeGreaterThan(job.bottom)
  await shot(owner, "workable")
  await expectFullHeightDialog(owner, owner.getByRole("main").getByTestId("instructions"))

  // A key that stopped working: Reconnect on its own line, on the page and on the tab.
  await markAtsBroken(company.id)
  await owner.reload()
  await expectReconnectOwnLine(owner.getByRole("main"))
  await shot(owner, "workable-broken")
  await visit(owner, tab)
  await expectReconnectOwnLine(integrationRow(owner, "/workable"))
  await shot(owner, "tab-broken")

  // The API: the docs and New key under the title.
  await visit(owner, `${tab}/api`)
  // The docs and New key.
  await expect(drawnButtons(owner.getByTestId("integration-actions"))).toHaveCount(2)
  await expectButtonsUnderTitle(owner)
  await shot(owner, "api")
})
