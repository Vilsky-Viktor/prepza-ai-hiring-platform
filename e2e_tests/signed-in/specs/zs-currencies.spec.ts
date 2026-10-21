import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { createCompany } from "../helpers/api"
import { PHONE } from "../helpers/layout"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { throwawayEmail } from "../helpers/users"

/** The visitor's country as the load balancer would give it: locally the gateway takes it from
 * this cookie. */
async function fromCountry(page: Page, country: string) {
  await page.context().addCookies([
    { name: "test_country", value: country, url: new URL(page.url()).origin },
  ])
}

/** Both themes of the page as it is now. */
async function shots(page: Page, name: string, fullPage = false) {
  for (const scheme of ["light", "dark"] as const) {
    await page.emulateMedia({ colorScheme: scheme })
    await shot(page, `${name}-${scheme}`, fullPage)
  }

  await page.emulateMedia({ colorScheme: "light" })
}

// A person's currency is saved from their country the first time billing sees them with one,
// shown on the settings page beside the language, and can be changed there; the site's prices
// then follow it wherever they are.
test("a person sees prices in their own saved currency", async ({ signInAs }) => {
  const page = await signInAs(throwawayEmail("currency-user"))
  await fromCountry(page, "DE")
  await visit(page, "/settings")
  await shots(page, "settings-eur", true)

  // In the EU, changed to US dollars.
  const mine = page.getByTestId("user-currency")
  await expect(mine).toHaveAttribute("data-currency", "EUR")
  await mine.getByRole("button").click()
  await page.getByRole("menuitemradio", { name: /USD/ }).click()
  await expect(mine).toHaveAttribute("data-currency", "USD")

  await visit(page, "/")
  await expect(page.getByTestId("hero-price")).toContainText("$")
  await shots(page, "home-eu-visitor-usd")
  await visit(page, "/pricing")
  await shots(page, "pricing-eu-visitor-usd", true)
})

// A company pays in its own currency whoever pays and wherever they are: its billing page sets
// it, and its top-up dialog prices in it and says so, even for someone who sees euros elsewhere.
test("a company's top-up is in the company's currency", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("currency-company"))
  await fromCountry(owner, "DE")
  const company = await createCompany(owner)
  await visit(owner, `/companies/${company.id}/billing`)
  const currency = owner.getByTestId("company-currency")
  await expect(currency).toHaveAttribute("data-currency", "EUR")
  await currency.getByRole("button").click()
  await owner.getByRole("menuitemradio", { name: /USD/ }).click()
  await expect(currency).toHaveAttribute("data-currency", "USD")
  await shots(owner, "billing-usd-company", true)

  await openDialog(owner, owner.getByTestId("top-up").first())
  await expect(owner.getByTestId("pays-in")).toHaveAttribute("data-currency", "USD")
  await shots(owner, "top-up-usd-company-eur-person", true)
  await owner.keyboard.press("Escape")

  // Elsewhere the person's own euros.
  await visit(owner, "/pricing")
  await expect(owner.getByRole("main")).toContainText("€")
  await shots(owner, "pricing-eur-person", true)

  // The top-up page has the same pill beside each company's Top up.
  await visit(owner, "/top-up")
  await expect(owner.getByTestId("company-currency").first()).toHaveAttribute(
    "data-currency",
    "USD",
    { timeout: 30_000 }
  )
  await shots(owner, "top-up-page", true)
  await owner.setViewportSize(PHONE)
  await shots(owner, "top-up-page-phone", true)
  await visit(owner, `/companies/${company.id}/billing`)
  await expect(currency).toHaveAttribute("data-currency", "USD")
  await shots(owner, "billing-phone")

})

// A company in pounds: its billing page and top-up price in pounds, and Paddle's checkout
// charges them.
test("a company in pounds is charged in pounds", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("currency-gbp"))
  await fromCountry(owner, "GB")
  const company = await createCompany(owner)
  await visit(owner, `/companies/${company.id}/billing`)
  await expect(owner.getByTestId("company-currency")).toHaveAttribute("data-currency", "GBP")
  await shots(owner, "billing-gbp", true)

  await openDialog(owner, owner.getByTestId("top-up").first())
  await expect(owner.getByTestId("pays-in")).toHaveAttribute("data-currency", "GBP")
  await shots(owner, "top-up-gbp", true)

  // Paddle's sandbox checkout charges pounds, wherever this browser is (nothing is paid).
  await expect(owner.getByRole("dialog").getByRole("slider")).toBeVisible()
  const buy = owner.getByRole("dialog").getByRole("button").first()
  test.skip(await buy.isDisabled(), "Paddle's product isn't set locally")
  await buy.click()
  const checkout = owner.frameLocator("iframe[name=paddle_frame]")
  await expect(checkout.getByText(/£/).first()).toBeVisible({ timeout: 30_000 })
  await shot(owner, "paddle-checkout-gbp", false)
})
