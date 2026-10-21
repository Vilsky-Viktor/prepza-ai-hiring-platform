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

/** The currency on the company's pill in `path`'s HTML as the server sends it, before any of
 * the page's scripts run; null without one. */
async function servedPill(page: Page, path: string) {
  const html = await (await page.request.get(path)).text()

  return /data-testid="company-currency" data-currency="(\w+)"/.exec(html)?.[1] ?? null
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

  // In the EU, changed to US dollars; the list is searched by name or code.
  const mine = page.getByTestId("user-currency")
  await expect(mine).toHaveAttribute("data-currency", "EUR")
  // The search field takes the focus as the list opens.
  await mine.getByRole("combobox").click()
  await page.locator("input:focus").fill("yen")
  await expect(page.getByRole("option")).toHaveCount(1)
  await expect(page.getByRole("option")).toContainText("JPY")
  await shots(page, "settings-search-yen")
  await page.locator("input:focus").fill("USD")
  await page.getByRole("option").first().click()
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
  // The pill comes with the page, so nothing beside it moves later (the balance moved from
  // under the pointer, closing its tooltip).
  await expect(servedPill(owner, `/companies/${company.id}/billing`)).resolves.toBe("EUR")
  await currency.getByRole("combobox").click()
  await shots(owner, "company-currency-list")
  await owner.locator("input:focus").fill("USD")
  await owner.getByRole("option").first().click()
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
  await expect(servedPill(owner, "/top-up")).resolves.toBe("USD")
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

// A company created from Canada pays in Canadian dollars: its billing page and top-up dialog.
test("a company in Canadian dollars is priced in them", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("currency-cad"))
  await fromCountry(owner, "CA")
  const company = await createCompany(owner)
  await visit(owner, `/companies/${company.id}/billing`)
  await expect(owner.getByTestId("company-currency")).toHaveAttribute("data-currency", "CAD")

  await openDialog(owner, owner.getByTestId("top-up").first())
  await expect(owner.getByTestId("pays-in")).toHaveAttribute("data-currency", "CAD")
  await expect(owner.getByRole("dialog").getByTestId("custom-quote")).toContainText("CA$70")
  await shots(owner, "top-up-cad", true)
})

// A company created from Japan pays in yen, whole yen as Paddle counts them.
test("a company in yen is priced in whole yen", async ({ signInAs }) => {
  const owner = await signInAs(throwawayEmail("currency-jpy"))
  await fromCountry(owner, "JP")
  const company = await createCompany(owner)
  await visit(owner, `/companies/${company.id}/billing`)
  await expect(owner.getByTestId("company-currency")).toHaveAttribute("data-currency", "JPY")

  await openDialog(owner, owner.getByTestId("top-up").first())
  await expect(owner.getByRole("dialog").getByTestId("custom-quote")).toContainText("¥7,500")
  await shots(owner, "top-up-jpy", true)
})
