import type { Page } from "@playwright/test"

import { expect, test } from "../fixtures"
import { createCompany } from "../helpers/api"
import { PHONE } from "../helpers/layout"
import { openDialog, visit } from "../helpers/navigation"
import { shot } from "../helpers/screenshots"
import { setScheme } from "../helpers/theme"
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
    await setScheme(page, scheme)
    await shot(page, `${name}-${scheme}`, fullPage)
  }

  await setScheme(page, "light")
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
  // The pill shows the choice at once, before billing has saved it: the home page, rendered by
  // the server, reads the saved one, so it opens once the save has answered.
  const saved = page.waitForResponse(
    (response) =>
      response.request().method() === "PUT" && response.url().endsWith("/billing/me/currency")
  )
  await page.getByRole("option").first().click()
  expect((await saved).ok()).toBe(true)
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

// Each currency's prices (whole yen included) and the checkout's currency are billing's unit
// tests (test_credits.py, test_custom_top_ups.py); how each is written is
// frontend/tests/lib/format.test.ts.
