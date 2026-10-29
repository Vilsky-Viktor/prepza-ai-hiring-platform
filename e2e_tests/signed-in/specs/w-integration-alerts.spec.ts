import type { Page } from "@playwright/test";

import { expect, test } from "../fixtures";
import { addCompanyNotification } from "../helpers/db-integrations";
import { visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { ownerEmail, randomId } from "../helpers/users";

/** A new company made on the companies page, as its owner makes one: the bell knows it at once
 * (it asks for the user's companies again), not a minute later. */
async function createCompanyHere(owner: Page) {
  await visit(owner, "/companies");
  await owner.getByTestId("new-company").click();
  await owner.getByRole("dialog").getByRole("textbox").fill(`E2E ${randomId()}`);
  await owner.getByRole("dialog").locator('button[type="submit"]').click();
  await expect(owner).toHaveURL(/\/companies\/[^/]+\/interviews$/);

  return { id: new URL(owner.url()).pathname.split("/")[2] };
}

/** Opens the bell on the company's interviews; its notification that leads to `page`, which
 * names `named` (what the notification was about) and shows as an alert (a red icon). */
async function bellAlert(owner: Page, companyId: string, page: string, named: string) {
  await visit(owner, `/companies/${companyId}/interviews`);
  await owner.getByTestId("notifications").click();
  const notice = owner.getByRole("menu").locator(`a[href$="${page}"]`);
  await expect(notice).toHaveCount(1);
  await expect(notice).toContainText(named);
  await expect(notice).toHaveAttribute("data-alert", "true");

  return notice;
}

// The company's bell says, in red, when an integration stopped working, and opens its page to
// reconnect: an ATS that takes the key but refuses the results written back, and a connection
// that stopped working (Slack's web hook gone, an ATS key revoked).
test("the bell says when an ATS or Slack stopped working", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompanyHere(owner);
  const integrations = `/companies/${company.id}/integrations`;
  const alerts = [
    { kind: "ats_cannot_write", page: `${integrations}/recruitee`, named: "Recruitee", data: { ats: "Recruitee" } },
    { kind: "connection_broken", page: `${integrations}/slack`, named: "Slack", data: { name: "Slack", integration: "slack" } },
  ];

  for (const { kind, page, data } of alerts) {
    await addCompanyNotification(company.id, kind, page, data);
  }

  for (const { page, named } of alerts) {
    const notice = await bellAlert(owner, company.id, page, named);
    await shot(owner, `bell-${named}`);
    await notice.click();
    await expect(owner).toHaveURL(new RegExp(`${page}$`));
  }
});
