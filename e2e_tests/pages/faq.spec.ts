import { expect, test } from "@playwright/test";

import { loaded } from "./helpers/waits";

// FAQ answers link to the site's own pages: a link opens its page in the same tab, in the
// language of the address it's on.

test("an answer's link opens its page in the same tab", async ({ page }) => {
  await page.goto("/faq");
  await loaded(page);
  const answer = page
    .getByRole("main")
    .locator("details")
    .filter({ has: page.locator('a[href="/pricing"]') });
  await answer.locator("summary").click();
  const link = answer.getByRole("link");

  await expect(link).toHaveAttribute("href", "/pricing");
  await expect(link).not.toHaveAttribute("target", /.+/);
  await link.click();
  await expect(page).toHaveURL(/\/pricing$/);
  expect(page.context().pages()).toHaveLength(1);
});

test("an answer's links stay in the address's language", async ({ page }) => {
  await page.goto("/de/faq");
  await loaded(page);
  // Every answer's links, closed answers' too.
  const links = page
    .getByRole("main")
    .locator("details")
    .getByRole("link", { includeHidden: true });
  const hrefs = await links.evaluateAll((items) =>
    items.map((item) => item.getAttribute("href")),
  );

  expect(hrefs).toContain("/de/pricing");
  expect(hrefs).toContain("/de/guides/ats-integration-skills-tests");
  expect(hrefs).not.toContain("/pricing");
});
