import { expect, test } from "../fixtures";
import { createCompany } from "../helpers/api";
import { DECLINED_CARD, openTopUpCheckout, payWith } from "../helpers/paddle";
import { shot } from "../helpers/screenshots";
import { ownerEmail } from "../helpers/users";

// A card Paddle's sandbox declines: its checkout closes and our dialog says why, as billing
// decided from Paddle's payment attempt. Try again opens the same checkout; Close closes. Needs
// Paddle's sandbox keys and prices in .env.
test("a declined card shows why and lets the buyer try again", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompany(owner);
  const checkout = owner.locator("iframe.paddle-frame");
  const failed = owner.getByTestId("payment-failed");

  await openTopUpCheckout(owner, company.id);
  await payWith(owner, DECLINED_CARD);

  await expect(failed).toBeVisible({ timeout: 60_000 });
  await expect(failed).toHaveAttribute("data-reason", "card_declined");
  await expect(checkout).toBeHidden();
  await shot(owner, "payment-failed");

  // Try again, the footer's last button: the same checkout opens over the page.
  await failed.getByRole("button").last().click();
  await expect(failed).toBeHidden();
  await payWith(owner, DECLINED_CARD);

  await expect(failed).toBeVisible({ timeout: 60_000 });
  // Close, the footer's first button.
  await failed.getByRole("button").first().click();
  await expect(failed).toBeHidden();
  await expect(checkout).toBeHidden();
});
