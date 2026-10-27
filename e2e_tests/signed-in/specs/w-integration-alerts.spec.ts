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

// An ATS that takes the key but refuses the results written back: the company's bell says so,
// in red, and opens that ATS's page to reconnect.
test("the bell says when an ATS doesn't take candidates' results", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompanyHere(owner);
  const page = `/companies/${company.id}/integrations/recruitee`;
  await addCompanyNotification(company.id, "ats_cannot_write", page, {
    ats: "Recruitee",
  });

  const notice = await bellAlert(owner, company.id, page, "Recruitee");
  await shot(owner, "bell");
  await notice.click();
  await expect(owner).toHaveURL(new RegExp(`${page}$`));
});

// A connection that stopped working (Slack's web hook gone, an ATS key revoked): the bell says
// what waits meanwhile and opens its page to reconnect.
test("the bell says when Slack stopped working", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompanyHere(owner);
  const page = `/companies/${company.id}/integrations/slack`;
  await addCompanyNotification(company.id, "connection_broken", page, {
    name: "Slack",
    integration: "slack",
  });

  const notice = await bellAlert(owner, company.id, page, "Slack");
  await shot(owner, "bell-slack");
  await notice.click();
  await expect(owner).toHaveURL(new RegExp(`${page}$`));
});

// A web hook whose member is no longer an owner or admin: the bell names it and opens the API
// page.
test("the bell says when a web hook stopped", async ({ signInAs }) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompanyHere(owner);
  const page = `/companies/${company.id}/integrations/api`;
  const url = "https://example.com/prepza";
  await addCompanyNotification(company.id, "webhook_stopped", page, { url });

  const notice = await bellAlert(owner, company.id, page, url);
  await shot(owner, "bell-webhook");
  await notice.click();
  await expect(owner).toHaveURL(new RegExp(`${page}$`));
});
