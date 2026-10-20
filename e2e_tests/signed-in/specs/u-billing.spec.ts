import type { Page } from "@playwright/test";

import { expect, test } from "../fixtures";
import {
  api,
  createCompany,
  createInterview,
  finishOneAnswer,
  inviteCandidate,
} from "../helpers/api";
import { addTopUp } from "../helpers/db";
import { openTab, visit } from "../helpers/navigation";
import { shot } from "../helpers/screenshots";
import { ownerEmail, throwawayEmail } from "../helpers/users";

/** The billing page's tab of the reserved candidates, which counts them. */
function reservedTab(page: Page) {
  return page.getByRole("main").locator('a[href$="?tab=reserved"]');
}

// A company's billing: owners and admins see where the credits came from and went, and the
// candidates whose credits are reserved; a viewer has no billing tab, and its address sends them
// back to the interviews.
test("owner sees the company's billing, a viewer doesn't", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompany(owner);
  const tabs = owner
    .getByRole("main")
    .getByRole("navigation")
    .getByRole("link");
  const history = owner
    .getByRole("main")
    .getByRole("list")
    .getByRole("listitem");
  const reserved = owner.getByTestId("reserved-credits");

  // The company's tabs include billing for its owner.
  await visit(owner, `/companies/${company.id}/interviews`);
  await expect(tabs.and(owner.locator('a[href$="/billing"]'))).toHaveCount(1);
  // A new company's history: the welcome gift's credits.
  await openTab(owner, "/billing");
  await expect(history).toHaveCount(1);
  await expect(history).toContainText("+1,500");
  await expect(reservedTab(owner)).toHaveText(/\b0\b/);
  // Nothing reserved yet: no "0 reserved" under the balance.
  await expect(reserved).toHaveCount(0);
  await shot(owner, "history");

  // An invited candidate holds credits until they finish.
  const interviewId = await createInterview(owner, company.id);
  const candidate = throwawayEmail("billing-candidate");
  await inviteCandidate(owner, interviewId, candidate);
  await visit(owner, `/companies/${company.id}/billing`);
  await expect(reserved).toContainText("500");
  await expect(reservedTab(owner)).toHaveText(/\b1\b/);
  await openTab(owner, "?tab=reserved");
  await expect(owner.getByText(candidate)).toBeVisible();
  await shot(owner, "reserved");

  // A viewer joins through their invite.
  const viewer = throwawayEmail("billing-viewer");
  const member = await api<{ token: string }>(
    owner,
    "POST",
    `/companies/members?company_id=${company.id}`,
    { email: viewer, role: "viewer" },
  );
  const page = await signInAs(viewer);
  await api(page, "POST", `/companies/members/invites/${member.token}/accept`);

  await visit(page, `/companies/${company.id}/interviews`);
  const viewerTabs = page.getByRole("main").getByRole("navigation");
  await expect(viewerTabs.locator('a[href$="/referrals"]')).toBeVisible();
  await expect(viewerTabs.locator('a[href$="/billing"]')).toHaveCount(0);
  await shot(page, "viewer-tabs");
  await visit(page, `/companies/${company.id}/billing`);
  await expect(page).toHaveURL(
    new RegExp(`/companies/${company.id}/interviews$`),
  );
});

// The history's rows for paid credits and spent ones: a top-up with what was paid and its
// invoice, and a candidate's charge, once they answer, led by the candidate and opening them.
test("the history lists a top-up and a candidate's charge", async ({
  signInAs,
}) => {
  const owner = await signInAs(ownerEmail());
  const company = await createCompany(owner);
  const interviewId = await createInterview(owner, company.id);
  const email = throwawayEmail("billing-charged");
  await inviteCandidate(owner, interviewId, email);
  await addTopUp(company.id, 2500, 5000);

  // The candidate answers one question and finishes, as the app's player does.
  const candidate = await signInAs(email);
  await finishOneAnswer(candidate, email);

  // The top-up: the credits and the price the test paid.
  const topUp = owner.getByRole("listitem").filter({ hasText: "+2,500" });
  const charge = owner.getByRole("link").filter({ hasText: email });

  // The charge comes once the scorecard is made.
  await expect(async () => {
    await visit(owner, `/companies/${company.id}/billing`);
    await expect(charge).toBeVisible({ timeout: 3_000 });
  }).toPass({ timeout: 90_000 });
  await expect(topUp).toContainText("$50");
  // Its invoice, the row's only button.
  await expect(topUp.getByRole("button")).toHaveCount(1);
  await expect(charge).toContainText("-500");
  await expect(reservedTab(owner)).toHaveText(/\b0\b/);
  await shot(owner, "history-top-up-and-charge");

  await charge.click();
  await expect(owner).toHaveURL(
    new RegExp(`/companies/${company.id}/interviews/${interviewId}/candidates/[^/?]+$`),
    { timeout: 90_000 },
  );
});
