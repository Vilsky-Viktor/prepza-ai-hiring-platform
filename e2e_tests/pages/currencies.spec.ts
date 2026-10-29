import { expect, test, type Page } from "@playwright/test";

import { shot } from "./helpers/screenshots";
import { setScheme } from "./helpers/theme";

// A signed-out visitor sees prices in their country's currency, the hero's price per candidate and
// the pricing page's list alike, as English writes them. Locally the gateway takes the country
// from a cookie, as the load balancer does from the address. Two countries here, one with a
// symbol and one written with its code; billing's unit tests (test_credits.py) map every country
// to its currency and frontend/tests/lib/format.test.ts writes each currency.

const COUNTRIES = [
  { country: "DE", symbol: "€" },
  { country: "PL", symbol: "PLN" },
];

async function fromCountry(page: Page, country: string) {
  await page.context().addCookies([
    { name: "test_country", value: country, url: test.info().project.use.baseURL! },
  ]);
}

for (const { country, symbol } of COUNTRIES) {
  test(`a visitor from ${country} sees prices in ${symbol}`, async ({ page }) => {
    await fromCountry(page, country);
    await page.goto("/");
    await expect(page.getByTestId("hero-price")).toContainText(symbol);

    for (const scheme of ["light", "dark"] as const) {
      await setScheme(page, scheme);
      await shot(page, `home-${country}-${scheme}`);
    }

    await page.goto("/pricing");
    await expect(page.getByRole("main")).toContainText(symbol);

    for (const scheme of ["light", "dark"] as const) {
      await setScheme(page, scheme);
      await shot(page, `pricing-${country}-${scheme}`, true);
    }
  });
}
