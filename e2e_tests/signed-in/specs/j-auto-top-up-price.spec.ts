import type { Page } from "@playwright/test";

import { expect, test as base } from "../fixtures";
import { createCompany } from "../helpers/api";
import {
  notifyCompany,
  removeAutoTopUp,
  setAutoTopUp,
} from "../helpers/auto-top-up";
import { mailText, mailsTo } from "../helpers/mailpit";
import { openDialog, visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { uidOf } from "../helpers/sign-in";
import { throwawayEmail } from "../helpers/users";

// The day a new price applies, 31 days ahead at midnight UTC, as billing sets it, and as the site
// writes it in English.
const NEXT_DAY = new Date(Date.UTC(2026, 10, 21)).toISOString();
const SHOWN_DAY = new Intl.DateTimeFormat("en", {
  dateStyle: "medium",
  timeZone: "UTC",
}).format(new Date(NEXT_DAY));

// A throwaway owner and company, whose automatic top-up row is removed before the company is.
const test = base.extend<{ owned: { page: Page; email: string; id: string } }>({
  owned: async ({ signInAs }, use) => {
    const email = throwawayEmail("auto-top-up-price");
    const page = await signInAs(email);
    const company = await createCompany(page);
    await use({ page, email, id: company.id });
    await removeAutoTopUp(company.id);
  },
});

// A new price announced: the setting shows what it charges now, and the new price with its day.
test("an announced new price shows beside the automatic top-up", async ({
  owned,
}) => {
  const { page, id } = owned;
  await setAutoTopUp(id, await uidOf(page), {
    price: 4500,
    nextPrice: 6000,
    nextFrom: NEXT_DAY,
  });

  await visit(page, "/top-up");
  await expect(page.getByTestId("auto-top-up-on")).toContainText("$45");
  const next = page.getByTestId("next-price");
  await expect(next).toContainText("$60");
  await expect(next).toContainText(SHOWN_DAY);
  await shot(page, "top-up-page");

  await visit(page, `/companies/${id}/billing`);
  await openDialog(page, page.getByTestId("top-up").first());
  await expect(
    page.getByTestId("auto-top-up").getByTestId("next-price"),
  ).toContainText("$60");
  await shot(page, "top-up-dialog");
});

// Choosing another currency applies at once: what each charge now costs in it, from billing, and
// the setting follows; the price announced in dollars no longer applies.
test("choosing another currency says what automatic top-up now charges", async ({
  owned,
}) => {
  const { page, id } = owned;
  await setAutoTopUp(id, await uidOf(page), {
    price: 4500,
    nextPrice: 6000,
    nextFrom: NEXT_DAY,
  });

  await visit(page, `/companies/${id}/billing`);
  await expect(page.getByTestId("next-price").filter({ visible: true })).toBeVisible();
  const currency = page.getByTestId("company-currency");
  await currency.getByRole("combobox").click();
  await page.locator("input:focus").fill("EUR");
  await page.getByRole("option").first().click();

  await expect(currency).toHaveAttribute("data-currency", "EUR");
  await expect(
    page.locator('[data-sonner-toast][data-type="success"]'),
  ).toContainText("€50");
  await expect(page.getByTestId("auto-top-up-on")).toContainText("€50");
  await expect(page.getByTestId("next-price")).toHaveCount(0);
  await shot(page, "currency-chosen");
});

// The notice: the bell and an email to the owner give both prices and the day, and open billing.
test("a new price is told in the bell and by email", async ({ owned }) => {
  const { page, email, id } = owned;
  const billing = `/companies/${id}/billing`;
  await notifyCompany(page.request, id, "auto_top_up_price_change", {
    price: 4500,
    new_price: 6000,
    currency: "USD",
    date: NEXT_DAY.slice(0, 10),
  });

  await expect
    .poll(async () => (await mailsTo(page.request, email)).length)
    .toBe(1);
  const [mail] = await mailsTo(page.request, email);
  const text = await mailText(page.request, mail.ID);
  expect(text).toContain("$45");
  expect(text).toContain("$60");
  expect(text).toContain(billing);

  await visit(page, `/companies/${id}/interviews`);
  await page.getByTestId("notifications").click();
  const notice = page.getByRole("menu").locator(`a[href$="${billing}"]`);
  await expect(notice).toContainText("$45");
  await expect(notice).toContainText("$60");
  await expect(notice).toContainText(SHOWN_DAY);
  await shot(page, "bell");
});
