import { expect, type Page, test } from "@playwright/test";

import { visit } from "./navigation";

// Paddle's sandbox test cards (developer.paddle.com, test cards): one that pays without a bank
// check, and one that is always declined.
export const PAYING_CARD = "4242424242424242";
export const DECLINED_CARD = "4000000000000002";

/** Opens Paddle's sandbox checkout for the smallest top-up from a company's billing page, or
 * skips the test when Paddle's prices aren't set. */
export async function openTopUpCheckout(page: Page, companyId: string) {
  await visit(page, `/companies/${companyId}/billing`);
  await page.getByTestId("top-up").first().click();
  // Its prices come as it opens: the slider shows once they have.
  await expect(page.getByTestId("top-up-dialog").getByRole("slider")).toBeVisible();
  // The Top up button, for the slider's first count (it comes before the dialog's other buttons).
  const buy = page.getByTestId("top-up-dialog").getByRole("button").first();
  test.skip(await buy.isDisabled(), "Paddle's prices aren't set");
  await buy.click();
}

/** Pays in the open Paddle checkout with `card`. */
export async function payWith(page: Page, card: string) {
  const checkout = page.frameLocator("iframe.paddle-frame");
  const number = checkout.locator('input[autocomplete="cc-number"]');
  await expect(number).toBeVisible({ timeout: 60_000 });
  const postcode = checkout.locator('input[autocomplete="postal-code"]');

  if (await postcode.isVisible()) {
    await postcode.fill("10001");
  }

  await number.fill(card);
  await checkout.locator('input[autocomplete="cc-name"]').fill("Test Buyer");
  await checkout.locator('input[autocomplete="cc-exp"]').fill("12/30");
  await checkout.locator('input[autocomplete="cc-csc"]').fill("100");
  await checkout.locator('button[type="submit"]').last().click();
}
