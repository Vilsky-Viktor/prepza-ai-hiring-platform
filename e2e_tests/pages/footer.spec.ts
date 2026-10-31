import { expect, test } from "@playwright/test";

// The company that runs prepza, as the footer and the contact page name it: its legal facts are
// data, not wording.
const OPERATOR = {
  name: "Arcolabs OÜ",
  registryCode: "17587452",
  address: "Sepapaja tn 6, 15551 Tallinn, Harju maakond, Estonia",
  email: "hello@prepza.ai",
};

async function hrefs(links: import("@playwright/test").Locator) {
  return links.evaluateAll((items) => items.map((item) => item.getAttribute("href")));
}

// The footer's links in three columns: the product, the features page and resources to read,
// and the company.
test("the footer groups its links by product, resources and company", { tag: "@phone" }, async ({ page }) => {
  await page.goto("/faq");
  const columns = page.getByRole("contentinfo").getByRole("navigation").getByRole("list");
  await expect(columns).toHaveCount(3);
  expect(await hrefs(columns.nth(0).getByRole("link"))).toEqual([
    "/tests",
    "/pre-employment-testing",
    "/ai-interviews",
    "/practice",
    "/compare",
  ]);
  expect(await hrefs(columns.nth(1).getByRole("link"))).toEqual([
    "/features",
    "/guides",
    "/faq",
    "/documents",
    "/api-docs",
    "/news",
  ]);
  expect(await hrefs(columns.nth(2).getByRole("link"))).toEqual([
    "/about",
    "/contact",
    "/trust",
    "/privacy",
    "/terms",
    "/accessibility",
  ]);

  // The menu is named for screen readers, and so is each social icon; the icons aren't links.
  const footer = page.getByRole("contentinfo");
  await expect(footer.getByRole("navigation")).toHaveAccessibleName(/.+/);

  for (const name of ["LinkedIn", "X", "YouTube", "Facebook"]) {
    await expect(footer.getByRole("img", { name, exact: true })).toBeVisible();
  }

  await expect(footer.locator('[role="img"]')).toHaveCount(4);
  await expect(footer.locator('a [role="img"]')).toHaveCount(0);
});

// The legal operator is within reach of every page: the footer names it, and the contact page
// gives its registry code, address and email.
test("the footer and the contact page name the company that runs prepza", async ({ page }) => {
  await page.goto("/contact");
  await expect(page.getByRole("contentinfo")).toContainText(
    `© ${new Date().getFullYear()} ${OPERATOR.name}`
  );
  const main = page.getByRole("main");

  for (const fact of Object.values(OPERATOR)) {
    await expect(main).toContainText(fact);
  }

  // The email is a link that writes to it.
  await expect(main.locator(`a[href="mailto:${OPERATOR.email}"]`)).toBeVisible();
});

// The accessibility statement says where to write, in the visitor's language.
test("the accessibility statement says where to report a problem", async ({ page }) => {
  await page.goto("/accessibility");
  const main = page.getByRole("main");
  await expect(main.locator(`a[href="mailto:${OPERATOR.email}"]`)).toBeVisible();
  const english = await main.getByRole("heading", { level: 1 }).textContent();

  await page.goto("/de/accessibility");
  await expect(page.locator("html")).toHaveAttribute("lang", "de");
  const german = page.getByRole("main").getByRole("heading", { level: 1 });
  await expect(german).not.toBeEmpty();
  await expect(german).not.toHaveText(english!);
  await expect(page.getByRole("main").locator(`a[href="mailto:${OPERATOR.email}"]`)).toBeVisible();
});
