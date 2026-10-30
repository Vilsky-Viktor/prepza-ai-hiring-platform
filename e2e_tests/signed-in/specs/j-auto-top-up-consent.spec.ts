import type { Page } from "@playwright/test";

import { BILLING_URL } from "../constants";
import { expect, test as base } from "../fixtures";
import { createCompany } from "../helpers/api";
import {
  notifyCompany,
  removeAutoTopUp,
  setAutoTopUp,
} from "../helpers/auto-top-up";
import { withDatabase } from "../helpers/db";
import { mailText, mailsTo } from "../helpers/mailpit";
import { openDialog, visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { uidOf } from "../helpers/sign-in";
import { throwawayEmail } from "../helpers/users";

// A throwaway owner and company, whose automatic top-up row is removed before the company is.
const test = base.extend<{ owned: { page: Page; email: string; id: string } }>({
  owned: async ({ signInAs }, use) => {
    const email = throwawayEmail("auto-top-up-consent");
    const page = await signInAs(email);
    const company = await createCompany(page);
    await use({ page, email, id: company.id });
    await removeAutoTopUp(company.id);
  },
});

// The buyer's tick, given in the dialog, is kept with the setting (when) and in the company's
// action log (who, and the terms agreed to).
test("a change is saved with the buyer's tick on its terms, which the action log keeps", async ({
  owned,
}) => {
  const { page, id } = owned;
  await setAutoTopUp(id, await uidOf(page), {});

  await visit(page, `/companies/${id}/billing`);
  const line = page.getByTestId("auto-top-up-on").filter({ visible: true });
  await openDialog(page, line.getByRole("button"));
  const setup = page.getByRole("dialog");
  const level = setup.locator("form").getByRole("button").nth(1);
  await level.click();
  await page.getByRole("menu").getByRole("menuitemradio").last().click();
  const save = setup.locator("button[type=submit]");
  await expect(save).toBeDisabled();
  await setup.getByTestId("auto-top-up-agree").click();
  await save.click();

  await expect(
    page.locator('[data-sonner-toast][data-type="success"]'),
  ).toBeVisible();
  const agreed = await withDatabase("billing", async (client) => {
    const { rows } = await client.query(
      "SELECT threshold, agreed_at FROM auto_top_ups WHERE owner_type = 'company' AND owner_id = $1",
      [id],
    );

    return rows[0];
  });
  expect(agreed.threshold).toBe(2500);
  expect(agreed.agreed_at).not.toBeNull();

  // Billing's scheduled publish, called now; the log shows the change with its terms.
  await page.request.post(`${BILLING_URL}/internal/schedules/outbox`);
  await expect(async () => {
    await visit(page, `/companies/${id}/actions`);
    const rows = page.getByRole("main").getByRole("listitem");
    await expect(rows.filter({ hasText: "2,500" })).toContainText("$50", {
      timeout: 2000,
    });
  }).toPass();
  await shot(page, "action-log-terms");
});

// Turned on and each charge: the bell and an email to the owner with what it charges, and the
// email opens the billing page where it's turned off.
test("turning it on and each charge are told in the bell and by email", async ({
  owned,
}) => {
  const { page, email, id } = owned;
  const billing = `/companies/${id}/billing`;
  await notifyCompany(page.request, id, "auto_top_up_on", {
    price: 5000,
    currency: "USD",
    threshold: 1500,
  });
  await notifyCompany(page.request, id, "auto_top_up_charged", {
    credits: 5000,
    price: 5450,
    currency: "USD",
    date: "2026-10-29",
    available: 5320,
  });

  await expect
    .poll(async () => (await mailsTo(page.request, email)).length)
    .toBe(2);
  const texts = await Promise.all(
    (await mailsTo(page.request, email)).map((mail) =>
      mailText(page.request, mail.ID),
    ),
  );
  const on = texts.find((text) => text.includes("1,500"))!;
  const charge = texts.find((text) => text.includes("5,320"))!;
  expect(on).toContain("$50");
  expect(on).toContain(billing);
  expect(charge).toContain("$54.50");
  expect(charge).toContain("5,000");
  expect(charge).toContain("October 29, 2026");
  expect(charge).toContain(billing);

  await visit(page, `/companies/${id}/interviews`);
  await page.getByTestId("notifications").click();
  const notices = page.getByRole("menu").locator(`a[href$="${billing}"]`);
  await expect(notices.filter({ hasText: "1,500" })).toContainText("$50");
  await expect(notices.filter({ hasText: "5,000" })).toHaveCount(1);
  await shot(page, "bell");
});
