import { expect, test } from "../fixtures";
import { createCompany } from "../helpers/api";
import { openTopUpCheckout, PAYING_CARD, payWith } from "../helpers/paddle";
import { shot } from "../helpers/screenshots";
import { ownerEmail } from "../helpers/users";

// A top-up paid in Paddle's sandbox checkout: once Paddle completes the payment, its checkout
// closes and the success dialog shows on the same page, with nothing added to the address, and
// the checkout doesn't come back. Needs Paddle's sandbox keys and prices in .env.
test("a completed payment shows the success dialog in place", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompany(owner);
  const checkout = owner.locator("iframe.paddle-frame");
  const paid = owner.getByTestId("paid-notice");

  await openTopUpCheckout(owner, company.id);
  await payWith(owner, PAYING_CARD);

  await expect(paid).toBeVisible({ timeout: 60_000 });
  await expect(paid).toHaveAttribute("data-paid", "top_up");
  await expect(checkout).toBeHidden();
  expect(new URL(owner.url()).pathname).toBe(
    `/companies/${company.id}/billing`,
  );
  expect(new URL(owner.url()).search).toBe("");
  await shot(owner, "paid-notice");

  // Close, in the dialog's footer.
  await paid.getByRole("button").last().click();
  await expect(paid).toBeHidden();
  await expect(checkout).toBeHidden();
});
