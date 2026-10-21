import { expect, test, type Page } from "@playwright/test";

// A signed-out visitor sees prices in their country's currency: euros in the EU (and Iceland,
// Liechtenstein, Norway, Switzerland), pounds in the UK, US dollars elsewhere; the hero's price
// per candidate and the pricing page's list alike. Locally the gateway takes the country from a
// cookie, as the load balancer does from the address.

const COUNTRIES = [
  { country: "DE", symbol: "€" },
  { country: "GB", symbol: "£" },
  { country: "US", symbol: "$" },
];

async function fromCountry(page: Page, country: string) {
  await page.context().addCookies([
    { name: "test_country", value: country, url: test.info().project.use.baseURL! },
  ]);
}

for (const { country, symbol } of COUNTRIES) {
  test(`a visitor from ${country} sees prices in ${symbol}`, async ({ page }) => {
    test.setTimeout(120_000);
    await fromCountry(page, country);
    await page.goto("/");
    await expect(page.getByTestId("hero-price")).toContainText(symbol);

    for (const scheme of ["light", "dark"] as const) {
      await page.emulateMedia({ colorScheme: scheme });
      await page.screenshot({
        path: test.info().outputPath(`home-${country}-${scheme}.png`),
        animations: "disabled",
      });
    }

    await page.goto("/pricing");
    await expect(page.getByRole("main")).toContainText(symbol);

    for (const scheme of ["light", "dark"] as const) {
      await page.emulateMedia({ colorScheme: scheme });
      await page.screenshot({
        path: test.info().outputPath(`pricing-${country}-${scheme}.png`),
        fullPage: true,
        animations: "disabled",
      });
    }
  });
}
