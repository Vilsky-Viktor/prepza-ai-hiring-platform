import { expect, test } from "../fixtures"
import { createCompany } from "../helpers/api"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

// The automatic top-up's amount and level are picked from the site's menu, not the browser's.
// It is offered only where Paddle is set up, so its setting is answered here as if it were.
test("an owner picks the automatic top-up's amount and level", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("auto-top-up"))
  await createCompany(owner)
  await owner.route("**/api/companies/companies/*/auto-top-up", (route) =>
    route.fulfill({
      json: {
        offered: true,
        on: false,
        waiting: false,
        product: null,
        threshold: null,
        products: ["topup_50", "topup_200"],
        thresholds: [500, 2000],
        currency: "USD",
        prices: { topup_50: 5000, topup_200: 20000 },
      },
    })
  )

  await visit(owner, "/top-up")
  // Off, it's a button that says what it does.
  await openDialog(owner, owner.getByTestId("set-up-auto-top-up"))
  const dialog = owner.getByRole("dialog")
  // Its two pills, the amount and the level, and no browser's select.
  const pills = dialog.locator("form").getByRole("button")
  await expect(pills).toHaveCount(2)
  await expect(owner.locator("select")).toHaveCount(0)
  await shot(owner, "dialog")

  for (const [index, name] of ["amount", "level"].entries()) {
    const pill = pills.nth(index)
    await pill.click()
    const items = owner.getByRole("menu").getByRole("menuitemradio")
    await expect(items.nth(1)).toBeVisible()
    await shot(owner, `menu-${name}`)
    // The option's first line: the amount (its candidates under it) or the level.
    const picked = (await items.last().innerText()).split("\n")[0]
    await items.last().click()
    await expect(owner.getByRole("menu")).toHaveCount(0)
    await expect(pill).toContainText(picked)
  }
})

// On, it's the setting as text, with the edit icon that changes it.
test("an automatic top-up that's on shows its setting and changes from the edit icon", async ({
  signInAs,
}) => {
  const owner = await signInAs(throwawayEmail("auto-top-up-on"))
  await createCompany(owner)
  await owner.route("**/api/companies/companies/*/auto-top-up", (route) =>
    route.fulfill({
      json: {
        offered: true,
        on: true,
        waiting: false,
        product: "topup_50",
        threshold: 500,
        products: ["topup_50", "topup_200"],
        thresholds: [500, 2000],
        currency: "USD",
        prices: { topup_50: 5000, topup_200: 20000 },
      },
    })
  )

  await visit(owner, "/top-up")
  // The setting: the amount and the level it was answered with.
  const setting = owner.getByTestId("auto-top-up-on")
  await expect(setting).toContainText("$50")
  await expect(setting).toContainText("500")
  await expect(owner.getByTestId("set-up-auto-top-up")).toHaveCount(0)
  await openDialog(owner, setting.getByRole("button"))
  await expect(owner.getByRole("dialog").locator("form").getByRole("button")).toHaveCount(2)
})
