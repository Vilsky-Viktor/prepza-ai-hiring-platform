import type { Page } from "@playwright/test";

import { expect, test as base } from "../fixtures";
import { createCompany } from "../helpers/api";
import {
  notifyCompany,
  removeAutoTopUp,
  setAutoTopUp,
} from "../helpers/auto-top-up";
import { PHONE } from "../helpers/layout";
import { mailText, mailsTo } from "../helpers/mailpit";
import { openDialog, visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { uidOf } from "../helpers/sign-in";
import { throwawayEmail } from "../helpers/users";

// Only the person whose card pays may update it (billing's refusal, word for word).
const NOT_YOUR_CARD =
  "Only the person whose card pays for it can change it. Turn it off, then turn it on with your own card.";

// A throwaway owner and company, whose automatic top-up row is removed before the company is.
const test = base.extend<{ owned: { page: Page; email: string; id: string } }>({
  owned: async ({ signInAs }, use) => {
    const email = throwawayEmail("auto-top-up-paused");
    const page = await signInAs(email);
    const company = await createCompany(page);
    await use({ page, email, id: company.id });
    await removeAutoTopUp(company.id);
  },
});

// A card that declined for good, or too often: the company's billing says it's paused, in red,
// with the button that updates the card; only the card's owner may.
test("a paused automatic top-up says so and offers to update the card", async ({
  owned,
}) => {
  const { page, id } = owned;
  // Paused on another member's card.
  await setAutoTopUp(id, "someone-else", { paused: true });

  await visit(page, "/top-up");
  const line = page.getByTestId("auto-top-up-on");
  await expect(line).toHaveAttribute("data-paused", "true");
  await shot(page, "top-up-page");

  await visit(page, `/companies/${id}/billing`);
  await openDialog(page, page.getByTestId("top-up").first());
  const card = page.getByTestId("auto-top-up");
  await expect(card).toHaveAttribute("data-paused", "true");
  await shot(page, "top-up-dialog");
  await page.setViewportSize(PHONE);
  await card.scrollIntoViewIfNeeded();
  await shot(page, "top-up-dialog-phone");

  await card.getByTestId("update-card").click();
  await expect(
    page.locator("[data-sonner-toast][data-type='error']"),
  ).toContainText(NOT_YOUR_CARD);
});

test("a running automatic top-up offers no card update", async ({ owned }) => {
  const { page, id } = owned;
  await setAutoTopUp(id, await uidOf(page), {});

  await visit(page, "/top-up");
  await expect(page.getByTestId("auto-top-up-on").filter({ visible: true })).toBeVisible();
  await expect(page.getByTestId("auto-top-up-on")).not.toHaveAttribute(
    "data-paused",
  );
  await expect(page.getByTestId("update-card")).toHaveCount(0);
});

// Pausing tells the company: the bell's alert opens its billing, and its owner gets an email
// with the same link, whatever their email settings.
test("a paused automatic top-up is told in the bell and by email", async ({
  owned,
}) => {
  const { page, email, id } = owned;
  const billing = `/companies/${id}/billing`;
  await notifyCompany(page.request, id, "auto_top_up_paused");

  await expect
    .poll(async () => (await mailsTo(page.request, email)).length)
    .toBe(1);
  const [mail] = await mailsTo(page.request, email);
  expect(await mailText(page.request, mail.ID)).toContain(billing);

  await visit(page, `/companies/${id}/interviews`);
  await page.getByTestId("notifications").click();
  const notice = page.getByRole("menu").locator(`a[href$="${billing}"]`);
  await expect(notice).toHaveCount(1);
  await expect(notice).toHaveAttribute("data-alert", "true");
  await shot(page, "bell");
});

// Running on another member's card: saving a change is refused, saying why.
test("only the card's owner changes a running automatic top-up", async ({
  owned,
}) => {
  const { page, id } = owned;
  await setAutoTopUp(id, "someone-else", {});

  await visit(page, `/companies/${id}/billing`);
  await openDialog(page, page.getByTestId("top-up").first());
  await page.getByTestId("auto-top-up").getByRole("button").last().click();
  const form = page.locator("#auto-top-up-form");
  // The level's pill: its last choice, the tick on its terms, then Save.
  await form.getByRole("button").last().click();
  await page.getByRole("menu").getByRole("menuitemradio").last().click();
  await form.getByTestId("auto-top-up-agree").click();
  await page.locator('button[type="submit"][form="auto-top-up-form"]').click();

  await expect(
    page.locator("[data-sonner-toast][data-type='error']"),
  ).toContainText(NOT_YOUR_CARD);
});
