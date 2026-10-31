import { expect, type Page, test } from "@playwright/test";

import { shot } from "./helpers/screenshots";
import { loaded } from "./helpers/waits";

const KEPT = "testee_ref";

async function referral(page: Page) {
  return (await page.context().cookies()).find((cookie) => cookie.name === KEPT);
}

/** The referral notice: a toast asking to keep the link, or to turn it down. */
function notice(page: Page) {
  return page.locator("[data-sonner-toast]").filter({ has: page.locator("button[data-action]") });
}

// A referral link is kept only once the visitor agrees (EU cookie consent).
test("a referral link asks before it's kept in a cookie", async ({ page }) => {
  await page.goto("/?ref=e2eRef01");
  await expect(notice(page)).toBeVisible();
  expect(await referral(page)).toBeUndefined();
  await shot(page, "referral-notice");

  await notice(page).locator("button[data-action]").click();
  expect((await referral(page))?.value).toBe("e2eRef01");

  // Kept: not asked again.
  await page.goto("/?ref=e2eRef01");
  await loaded(page);
  await expect(notice(page)).toHaveCount(0);
});

test("turning a referral link down keeps nothing", async ({ page }) => {
  await page.goto("/?ref=e2eRef02");
  await notice(page).locator("button[data-cancel]").click();
  expect(await referral(page)).toBeUndefined();

  // A code that doesn't read right isn't offered.
  await page.goto("/?ref=bad!");
  await loaded(page);
  await expect(notice(page)).toHaveCount(0);
});
