import { expect, type Page, test } from "@playwright/test";

import { env } from "./env";
import { visit } from "./navigation";

// Paddle's sandbox test cards (developer.paddle.com, test cards): one that pays without a bank
// check, and one that is always declined.
export const PAYING_CARD = "4242424242424242";
export const DECLINED_CARD = "4000000000000002";

// The error code of an attempt Paddle's sandbox payment processor failed on its side (it times
// out now and then); the next attempt on the same transaction goes through.
const PROCESSOR_ERROR = "psp_error";

/** Opens Paddle's sandbox checkout for the smallest top-up from a company's billing page, or
 * skips the test when Paddle's prices aren't set. Returns the checkout's Paddle transaction. */
export async function openTopUpCheckout(page: Page, companyId: string): Promise<string> {
  await visit(page, `/companies/${companyId}/billing`);
  await page.getByTestId("top-up").first().click();
  // Its prices come as it opens: the slider shows once they have.
  await expect(page.getByTestId("top-up-dialog").getByRole("slider")).toBeVisible();
  // The Top up button, for the slider's first count (it comes before the dialog's other buttons).
  const buy = page.getByTestId("top-up-dialog").getByRole("button").first();
  test.skip(await buy.isDisabled(), "Paddle's prices aren't set");
  const made = page.waitForResponse(
    (response) =>
      response.url().endsWith(`/companies/${companyId}/billing/checkout`) &&
      response.request().method() === "POST",
  );
  await buy.click();

  return (await (await made).json()).transaction_id;
}

/** The error code of the latest failed payment attempt on a transaction, once Paddle's sandbox
 * API has it (it can come a moment after the checkout reports the failure). */
async function failedAttemptCode(page: Page, transactionId: string): Promise<string> {
  let code: string | undefined;

  await expect(async () => {
    const response = await page.request.get(
      `https://sandbox-api.paddle.com/transactions/${transactionId}`,
      { headers: { Authorization: `Bearer ${env("PADDLE_API_KEY")}` } },
    );
    expect(response.ok()).toBe(true);
    const payments: { error_code: string | null }[] = (await response.json()).data.payments;
    code = payments.find((payment) => payment.error_code)?.error_code ?? undefined;
    expect(code).toBeDefined();
  }).toPass({ timeout: 30_000 });

  return code!;
}

/** How many payment attempts Paddle's sandbox API has on a transaction. */
export async function paymentAttempts(page: Page, transactionId: string): Promise<number> {
  const response = await page.request.get(
    `https://sandbox-api.paddle.com/transactions/${transactionId}`,
    { headers: { Authorization: `Bearer ${env("PADDLE_API_KEY")}` } },
  );
  expect(response.ok()).toBe(true);

  return ((await response.json()).data.payments ?? []).length;
}

/** Pays the open checkout of `transactionId` with the paying card. When the failure dialog
 * shows instead, only an error of Paddle's sandbox processor is tried once more (Try again
 * opens the same checkout); any other code fails the test, named. */
export async function payWithPayingCard(page: Page, transactionId: string) {
  const paid = page.getByTestId("paid-notice");
  const failed = page.getByTestId("payment-failed");
  await payWith(page, PAYING_CARD);
  // The processor's error takes about a minute to come.
  await expect(paid.or(failed)).toBeVisible({ timeout: 90_000 });

  if (await failed.isVisible()) {
    expect(await failedAttemptCode(page, transactionId), "Paddle's error code").toBe(
      PROCESSOR_ERROR,
    );
    await failed.getByRole("button").last().click();
    await payWith(page, PAYING_CARD);
  }
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
