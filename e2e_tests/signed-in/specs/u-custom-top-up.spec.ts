import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { createCompany } from "../helpers/api"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

/** The company's top-up dialog, from its billing tab. */
async function openTopUp(page: Page, companyId: string) {
  await visit(page, `/companies/${companyId}/billing`)
  await openDialog(page, page.getByTestId("top-up").first())

  return page.getByRole("dialog")
}

// Any number of candidates, priced from billing's catalog: price, credits and candidates, and
// the next level instead where it costs no more.
test("the top-up dialog prices any number of candidates", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("custom-top-up"))
  const company = await createCompany(owner)
  const dialog = await openTopUp(owner, company.id)
  const slider = dialog.getByRole("slider")
  const count = dialog.getByTestId("custom-count")
  const cards = dialog.getByTestId("custom-quote").locator("p")

  await slider.focus()
  await owner.keyboard.press("Home")
  await expect(count).toHaveText("10")
  await expect(cards.nth(0)).toHaveText("$50")
  await expect(cards.nth(1)).toContainText("5K")
  await expect(cards.nth(2)).toContainText("10")
  await expect(dialog.getByTestId("custom-upgraded")).toHaveCount(0)

  // Arrow keys move one candidate, in the small first level too.
  for (let step = 0; step < 29; step++) {
    await owner.keyboard.press("ArrowRight")
  }

  await expect(count).toHaveText("39")
  await expect(cards.nth(0)).toHaveText("$195")
  await expect(dialog.getByTestId("custom-upgraded")).toHaveCount(0)

  // 40 at $5 would cost $200, what 50 at $4 cost: those 50 it is.
  await owner.keyboard.press("ArrowRight")
  await expect(count).toHaveText("40")
  await expect(slider).toHaveAttribute("aria-valuetext", /40/)
  await expect(cards.nth(0)).toHaveText("$200")
  await expect(cards.nth(1)).toContainText("25K")
  await expect(cards.nth(2)).toContainText("50")
  await expect(dialog.getByTestId("custom-upgraded")).toContainText("50")
  await shot(owner, "next-level")

  await owner.keyboard.press("End")
  await expect(count).toHaveText("1,000")
  await expect(cards.nth(0)).toHaveText("$2,000")
  await expect(cards.nth(2)).toContainText("1K")

  // The button asks billing for the count shown; billing sets the price.
  await owner.keyboard.press("Home")

  for (let step = 0; step < 35; step++) {
    await owner.keyboard.press("ArrowRight")
  }

  const buy = dialog.getByRole("button").first()
  test.skip(await buy.isDisabled(), "Paddle's per-candidate prices aren't set")

  const sent: unknown[] = []
  await owner.route("**/billing/checkout", (route) => {
    sent.push(route.request().postDataJSON())

    return route.fulfill({ status: 503, json: { detail: "Unavailable" } })
  })
  await buy.click()
  await expect(owner.locator("[data-sonner-toast][data-type=error]")).toBeVisible()
  expect(sent).toEqual([{ candidates: 50 }])
})

const AUTO_TOP_UP = {
  offered: true,
  waiting: false,
  products: ["topup_50", "topup_200"],
  thresholds: [500, 2000],
  currency: "USD",
  prices: { topup_50: 5000, topup_200: 20000 },
}

// Under the button, the automatic top-up as a card; its dialog saves only a change.
test("the automatic top-up card changes the setting it shows", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("custom-top-up-auto"))
  const company = await createCompany(owner)
  await owner.route("**/api/companies/companies/*/auto-top-up", (route) =>
    route.fulfill({
      json: { ...AUTO_TOP_UP, on: true, product: "topup_50", threshold: 500 },
    })
  )
  const dialog = await openTopUp(owner, company.id)
  const card = dialog.getByTestId("auto-top-up")

  await expect(card.getByTestId("auto-top-up-on")).toContainText("$50")
  await expect(card.getByTestId("auto-top-up-on")).toContainText("500")
  await card.getByRole("button").click()
  // The setup's dialog, over the top-up's (which is then hidden from the accessibility tree).
  const setup = owner.getByRole("dialog")
  await expect(setup.locator("form")).toBeVisible()
  const footer = setup.locator("[data-slot=dialog-footer]").getByRole("button")
  const save = setup.locator("button[type=submit]")

  // Turn off, Close and Save; nothing to save until something changes.
  await expect(footer).toHaveCount(3)
  await expect(save).toBeDisabled()
  const amount = setup.locator("form").getByRole("button").first()
  await expect(amount).toContainText("$50")
  await expect(amount).toContainText("10")
  await shot(owner, "auto-top-up")

  await amount.click()
  await owner.getByRole("menu").getByRole("menuitemradio").last().click()
  await expect(amount).toContainText("$200")
  await expect(amount).toContainText("50")
  await expect(save).toBeEnabled()

  await amount.click()
  await owner.getByRole("menu").getByRole("menuitemradio").first().click()
  await expect(save).toBeDisabled()
})

test("an automatic top-up that's off is set up from its card", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("custom-top-up-off"))
  const company = await createCompany(owner)
  await owner.route("**/api/companies/companies/*/auto-top-up", (route) =>
    route.fulfill({
      json: { ...AUTO_TOP_UP, on: false, product: null, threshold: null },
    })
  )
  const dialog = await openTopUp(owner, company.id)

  await dialog.getByTestId("set-up-auto-top-up").click()
  const setup = owner.getByRole("dialog")
  await expect(setup.locator("form")).toBeVisible()

  // Close and Turn on, which needs no change.
  await expect(setup.locator("[data-slot=dialog-footer]").getByRole("button")).toHaveCount(2)
  await expect(setup.locator("button[type=submit]")).toBeEnabled()
})
